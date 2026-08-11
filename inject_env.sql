INSERT INTO environment_variables (key, value, uuid, resourceable_type, resourceable_id, version, is_preview, is_shown_once, is_multiline, is_literal, is_required, is_shared, is_runtime, is_buildtime, created_at, updated_at)
VALUES 
('VECTOR_SERVICE_URL', 'http://veklom-vector-service:8095', gen_random_uuid()::varchar, 'App\Models\Application', 21, '4.0.0-beta.239', false, false, false, false, false, false, true, true, NOW(), NOW()),
('VECTOR_DB_URL', 'postgresql://user:pass@llwfyzhnft87bz6brddiax1z:5432/veklom_vectors', gen_random_uuid()::varchar, 'App\Models\Application', 21, '4.0.0-beta.239', false, false, false, false, false, false, true, true, NOW(), NOW()),
('MCP_MESH_URL', 'http://capi-container:3003/mcp', gen_random_uuid()::varchar, 'App\Models\Application', 21, '4.0.0-beta.239', false, false, false, false, false, false, true, true, NOW(), NOW());
