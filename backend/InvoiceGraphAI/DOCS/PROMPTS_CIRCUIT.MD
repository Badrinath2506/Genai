Here are all possible request formats for testing the Circuit Query MockAPI, covering various query types and scenarios:

### 1. Basic Count Queries
```json
{
  "query": "How many circuits exist?",
  "count_only": true
}
```

```json
{
  "query": "Count all circuits for Acme Corp"
}
```

### 2. Invoice Number Queries
```json
{
  "query": "Find circuits with invoice number INV-2023-001"
}
```

```json
{
  "query": "Count circuits associated with invoice INV-2023-003",
  "count_only": true
}
```

### 3. Circuit ID Queries
```json
{
  "query": "Show details for circuit CIRC-002"
}
```

```json
{
  "query": "How many circuits have ID CIRC-001?",
  "count_only": true
}
```

### 4. Customer-Specific Queries
```json
{
  "query": "List all circuits for customer Globex Inc"
}
```

```json
{
  "query": "Count circuits where customer is Acme Corp",
  "count_only": true
}
```

### 5. Combined Filter Queries
```json
{
  "query": "Find circuits for Acme Corp with invoice INV-2023-003"
}
```

```json
{
  "query": "Show circuits with ID CIRC-002 for customer Globex Inc"
}
```

### 6. Partial Match Queries
```json
{
  "query": "Find circuits where invoice contains '2023'"
}
```

```json
{
  "query": "Show circuits where customer name starts with 'Acm'"
}
```

### 7. Edge Cases
```json
{
  "query": "Find circuits with non-existent invoice XYZ-999",
  "count_only": false
}
```

```json
{
  "query": "Show circuits for unknown customer",
  "count_only": false
}
```

### 8. Malformed Queries (for error handling)
```json
{
  "query": "",
  "count_only": true
}
```

```json
{
  "query": "Find circuits with invalid characters @#$%"
}
```

### Sample cURL Commands:

1. **Basic count query**:
```bash
curl -X POST http://localhost:8001/query \
-H "Content-Type: application/json" \
-d '{"query":"Count circuits for Acme Corp","count_only":true}'
```

2. **Detailed circuit lookup**:
```bash
curl -X POST http://localhost:8001/query \
-H "Content-Type: application/json" \
-d '{"query":"Show circuits with ID CIRC-002"}'
```

3. **Combined filter query**:
```bash
curl -X POST http://localhost:8001/query \
-H "Content-Type: application/json" \
-d '{"query":"Find circuits for Globex Inc with invoice INV-2023-002"}'
```

### Expected Response Patterns:

1. **Count responses** will return:
```json
{
  "response": "There are X circuits that match your request."
}
```

2. **Detail responses** will return:
```json
{
  "response": "I found X matching circuit records. Here's the detailed list:\n\n| Invoice Number | Customer Name | Circuit ID |\n|----------------|---------------|------------|\n| ... | ... | ... |"
}
```

3. **No matches** will return:
```json
{
  "response": "No matching circuits found."
}
```

4. **Error responses** will return appropriate HTTP status codes (400, 500, etc.) with error details.

These prompts cover all the key functionality of the Circuit Query API including filtering by all available fields, combined filters, count vs detail modes, and error scenarios.