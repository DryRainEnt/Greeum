"""
Project Manager for Greeum v5.0
Maps projects to branches for explicit context management

Design principle: Project = Branch (명시적 프로젝트 지정)
- No more automatic branch classification
- User explicitly sets current project
- All insights stored under current project
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class Project:
    """Project metadata"""
    name: str
    description: Optional[str] = None
    branch_root: Optional[str] = None  # Root hash for this project's branch
    block_count: int = 0
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    is_current: bool = False


class ProjectManager:
    """
    Manages projects as explicit branch mappings.

    v5.0 Design:
    - Project name → Branch root hash
    - Current project tracked in session
    - Cross-project search supported
    """

    DEFAULT_PROJECT = "_default"

    def __init__(self, db_manager):
        """
        Initialize ProjectManager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self._current_project: Optional[str] = None
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create projects table if not exists."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                name TEXT PRIMARY KEY,
                description TEXT,
                branch_root TEXT,
                created_at TEXT NOT NULL,
                last_activity TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        self.db_manager.conn.commit()

    def create_project(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name (unique)
            description: Optional description

        Returns:
            Created Project instance
        """
        now = datetime.now().isoformat()
        cursor = self.db_manager.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO projects (name, description, created_at, last_activity)
                VALUES (?, ?, ?, ?)
            """, (name, description, now, now))
            self.db_manager.conn.commit()

            logger.info(f"Created project: {name}")
            return Project(
                name=name,
                description=description,
                created_at=now,
                last_activity=now
            )

        except Exception as e:
            if "UNIQUE constraint" in str(e):
                logger.warning(f"Project already exists: {name}")
                return self.get_project(name)
            raise

    def get_project(self, name: str) -> Optional[Project]:
        """Get project by name."""
        cursor = self.db_manager.conn.cursor()

        cursor.execute("""
            SELECT name, description, branch_root, created_at, last_activity
            FROM projects
            WHERE name = ? AND is_active = 1
        """, (name,))

        row = cursor.fetchone()
        if not row:
            return None

        # Get block count
        block_count = self._get_block_count(row[2]) if row[2] else 0

        return Project(
            name=row[0],
            description=row[1],
            branch_root=row[2],
            created_at=row[3],
            last_activity=row[4],
            block_count=block_count,
            is_current=(row[0] == self._current_project)
        )

    def _get_block_count(self, branch_root: str) -> int:
        """Get number of blocks in a branch."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM blocks WHERE root = ?
        """, (branch_root,))
        row = cursor.fetchone()
        return row[0] if row else 0

    def list_projects(self, include_stats: bool = True) -> List[Project]:
        """List all active projects."""
        cursor = self.db_manager.conn.cursor()

        cursor.execute("""
            SELECT name, description, branch_root, created_at, last_activity
            FROM projects
            WHERE is_active = 1
            ORDER BY last_activity DESC
        """)

        projects = []
        for row in cursor.fetchall():
            block_count = 0
            if include_stats and row[2]:
                block_count = self._get_block_count(row[2])

            projects.append(Project(
                name=row[0],
                description=row[1],
                branch_root=row[2],
                created_at=row[3],
                last_activity=row[4],
                block_count=block_count,
                is_current=(row[0] == self._current_project)
            ))

        return projects

    def set_current_project(self, name: str) -> bool:
        """
        Set the current working project.

        Args:
            name: Project name

        Returns:
            True if successful
        """
        # Check if project exists
        project = self.get_project(name)
        if not project:
            # Auto-create if not exists
            project = self.create_project(name)

        self._current_project = name
        self._update_activity(name)
        logger.info(f"Current project set to: {name}")
        return True

    def get_current_project(self) -> Optional[str]:
        """Get current project name."""
        return self._current_project

    def get_current_project_details(self) -> Optional[Project]:
        """Get current project with full details."""
        if not self._current_project:
            return None
        return self.get_project(self._current_project)

    def update_project(
        self,
        name: str,
        description: Optional[str] = None,
        branch_root: Optional[str] = None
    ) -> bool:
        """Update project metadata."""
        cursor = self.db_manager.conn.cursor()

        updates = []
        params = []

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if branch_root is not None:
            updates.append("branch_root = ?")
            params.append(branch_root)

        if not updates:
            return False

        updates.append("last_activity = ?")
        params.append(datetime.now().isoformat())
        params.append(name)

        cursor.execute(f"""
            UPDATE projects
            SET {", ".join(updates)}
            WHERE name = ?
        """, params)

        self.db_manager.conn.commit()
        return cursor.rowcount > 0

    def _update_activity(self, name: str) -> None:
        """Update last activity timestamp."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            UPDATE projects SET last_activity = ? WHERE name = ?
        """, (datetime.now().isoformat(), name))
        self.db_manager.conn.commit()

    def delete_project(self, name: str, hard_delete: bool = False) -> bool:
        """
        Delete a project (soft delete by default).

        Args:
            name: Project name
            hard_delete: If True, permanently delete

        Returns:
            True if deleted
        """
        cursor = self.db_manager.conn.cursor()

        if hard_delete:
            cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
        else:
            cursor.execute("""
                UPDATE projects SET is_active = 0 WHERE name = ?
            """, (name,))

        self.db_manager.conn.commit()

        if self._current_project == name:
            self._current_project = None

        return cursor.rowcount > 0

    def link_branch_to_project(self, name: str, branch_root: str) -> bool:
        """
        Link a branch root hash to a project.

        Called when first block is created in a project.
        """
        return self.update_project(name, branch_root=branch_root)

    def get_project_for_branch(self, branch_root: str) -> Optional[str]:
        """Get project name for a branch root hash."""
        cursor = self.db_manager.conn.cursor()
        cursor.execute("""
            SELECT name FROM projects WHERE branch_root = ? AND is_active = 1
        """, (branch_root,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_or_create_project(self, name: str) -> Project:
        """Get existing project or create new one."""
        project = self.get_project(name)
        if not project:
            project = self.create_project(name)
        return project

    def search_projects(self, query: str) -> List[Project]:
        """Search projects by name or description."""
        cursor = self.db_manager.conn.cursor()
        pattern = f"%{query}%"

        cursor.execute("""
            SELECT name, description, branch_root, created_at, last_activity
            FROM projects
            WHERE is_active = 1 AND (name LIKE ? OR description LIKE ?)
            ORDER BY last_activity DESC
        """, (pattern, pattern))

        projects = []
        for row in cursor.fetchall():
            projects.append(Project(
                name=row[0],
                description=row[1],
                branch_root=row[2],
                created_at=row[3],
                last_activity=row[4],
                is_current=(row[0] == self._current_project)
            ))

        return projects

    def get_stats(self) -> Dict[str, Any]:
        """Get project manager statistics."""
        cursor = self.db_manager.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM projects WHERE is_active = 1")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM projects
            WHERE is_active = 1 AND branch_root IS NOT NULL
        """)
        with_blocks = cursor.fetchone()[0]

        return {
            "total_projects": total,
            "projects_with_blocks": with_blocks,
            "current_project": self._current_project
        }
