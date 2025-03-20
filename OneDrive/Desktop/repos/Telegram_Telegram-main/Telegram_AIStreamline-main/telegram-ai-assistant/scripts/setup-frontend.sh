#!/bin/bash

# Navigate to frontend directory
cd frontend

# Install Supabase and other required dependencies
npm install @supabase/supabase-js@latest
npm install @supabase/auth-helpers-nextjs@latest
npm install @supabase/auth-helpers-react@latest

# Install dev dependencies
npm install -D @types/node@latest
npm install -D @types/react@latest
npm install -D @types/react-dom@latest

# Create .env.local file with placeholder values
cat > .env.local << EOL
NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
NEXT_PUBLIC_SUPABASE_KEY=your-supabase-anon-key
EOL

echo "Frontend setup completed! Please update .env.local with your Supabase credentials."
