
-- Create additional indexes for better performance

-- Notes full-text search indexes (if not created by triggers)
CREATE INDEX IF NOT EXISTS idx_notes_content_search ON notes(content);

-- Document processing optimization indexes
CREATE INDEX IF NOT EXISTS idx_documents_type_status ON documents(file_type, processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_size ON documents(file_size);

-- Knowledge graph optimization indexes
CREATE INDEX IF NOT EXISTS idx_kg_nodes_composite ON kg_nodes(node_type, label);
CREATE INDEX IF NOT EXISTS idx_kg_edges_composite ON kg_edges(relation_type, weight);

-- Search history optimization
CREATE INDEX IF NOT EXISTS idx_search_mode_time ON search_history(search_mode, created_at);

-- Background tasks optimization
CREATE INDEX IF NOT EXISTS idx_tasks_type_status ON background_tasks(task_type, status);
CREATE INDEX IF NOT EXISTS idx_tasks_progress ON background_tasks(progress);

-- Create views for common queries
CREATE VIEW IF NOT EXISTS active_documents AS
SELECT * FROM documents 
WHERE processing_status IN ('queued', 'processing', 'completed');

CREATE VIEW IF NOT EXISTS recent_notes AS
SELECT * FROM notes 
ORDER BY updated_at DESC 
LIMIT 100;

CREATE VIEW IF NOT EXISTS graph_summary AS
SELECT 
    node_type,
    COUNT(*) as node_count
FROM kg_nodes 
GROUP BY node_type;
