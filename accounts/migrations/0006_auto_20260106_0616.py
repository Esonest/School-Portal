
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_contactmessage'),  # replace with your latest migration
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE accounts_user
                DROP CONSTRAINT IF EXISTS accounts_user_username_key;
            """,
            reverse_sql="""
                ALTER TABLE accounts_user
                ADD CONSTRAINT accounts_user_username_key UNIQUE (username);
            """
        ),
    ]
