<% 
from alembic import util
%>
"""Auto-generated Alembic migration template."""

revision = '${up_revision}'
down_revision = ${repr(down_revision) if down_revision else None}
branch_labels = ${repr(branch_labels) if branch_labels else None}
depends_on = ${repr(depends_on) if depends_on else None}

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass


def downgrade():
    pass
