#!/bin/bash
# Update .env file with Mailtrap credentials

ENV_FILE=".env"

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    touch "$ENV_FILE"
fi

# Remove old mail settings if they exist
sed -i '/^MAIL_/d' "$ENV_FILE"
sed -i '/^# Mail/d' "$ENV_FILE"
sed -i '/^# Email/d' "$ENV_FILE"

# Add Mailtrap settings
cat >> "$ENV_FILE" << EOF

# ============================================
# Mail/Email Settings (Mailtrap for Testing)
# ============================================
MAIL_USERNAME=71cb026f5e49db
MAIL_PASSWORD=3b503193acb006
MAIL_FROM=noreply@fastship.com
MAIL_PORT=2525
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_FROM_NAME=FastShip
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=False
EOF

echo "✅ .env file updated with Mailtrap credentials"
