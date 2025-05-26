# Installing Apache AGE for Knowledge Graph Support

Apache AGE (A Graph Extension) is required for the LightRAG knowledge graph functionality. This guide shows how to install it.

## Prerequisites

- PostgreSQL 11, 12, 13, 14, or 15
- PostgreSQL development headers (postgresql-server-dev-XX)

## Installation Methods

### Option 1: Using Package Manager (Ubuntu/Debian)

```bash
# Add AGE repository
sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:postgresql/postgresql

# Install PostgreSQL development files (replace 15 with your version)
sudo apt-get install postgresql-server-dev-15

# Install build dependencies
sudo apt-get install build-essential libreadline-dev zlib1g-dev flex bison

# Clone and build AGE
git clone https://github.com/apache/age.git
cd age
git checkout release/PG15/1.5.0  # Use appropriate version for your PostgreSQL

# Build and install
make
sudo make install
```

### Option 2: Using Docker (Recommended)

Use a PostgreSQL image with AGE pre-installed:

```dockerfile
FROM apache/age:PG15_latest

# Your additional setup here
```

Or in docker-compose.yml:

```yaml
services:
  postgres:
    image: apache/age:PG15_latest
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: lightrag
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### Option 3: Build from Source

```bash
# Download source
wget https://github.com/apache/age/archive/refs/tags/PG15/v1.5.0.tar.gz
tar -xzf v1.5.0.tar.gz
cd age-PG15-v1.5.0

# Configure and build
make PG_CONFIG=/usr/bin/pg_config
sudo make install
```

## Enabling AGE in Your Database

After installation, enable AGE in your database:

```sql
-- Connect to your database
\c lightrag

-- Create the extension
CREATE EXTENSION age;

-- Load the extension
LOAD 'age';

-- Set the search path
SET search_path = ag_catalog, "$user", public;

-- Create your graph
SELECT ag_catalog.create_graph('lightrag_graph');
```

## Verifying Installation

Test that AGE is working:

```sql
-- Should return the AGE version
SELECT age_version();

-- Create a test node
SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
CREATE (n:TestNode {name: 'test'})
RETURN n
$$) as (n agtype);

-- Query the test node
SELECT * FROM ag_catalog.cypher('lightrag_graph', $$
MATCH (n:TestNode)
RETURN n
$$) as (n agtype);
```

## Troubleshooting

### "Extension 'age' is not available"

Make sure AGE is properly installed and the .so files are in the PostgreSQL lib directory:

```bash
# Find PostgreSQL lib directory
pg_config --pkglibdir

# Check if age.so exists
ls $(pg_config --pkglibdir)/age.so
```

### "Graph 'lightrag_graph' does not exist"

Create the graph first:

```sql
SELECT ag_catalog.create_graph('lightrag_graph');
```

### Permission Issues

Grant necessary permissions:

```sql
GRANT USAGE ON SCHEMA ag_catalog TO your_user;
GRANT ALL ON ALL TABLES IN SCHEMA ag_catalog TO your_user;
```

## Without AGE

If you can't install AGE, the MCP server will still work but without knowledge graph functionality. Only the document search features will be available.
