Here are all possible prompts with request bodies you can use to test the Invoice Query MockAPI:

### 1. Simple Count Queries
```json
{
  "query": "How many invoices exist?",
  "count_only": true
}
```

```json
{
  "query": "Count all invoices for Acme Corp"
}
```

### 2. Date-Based Queries
```json
{
  "query": "Show invoices from year 2023"
}
```

```json
{
  "query": "List invoices between January 2023 and March 2023"
}
```

```json
{
  "query": "Count invoices from month 02 in 2023",
  "count_only": true
}
```

### 3. Customer-Specific Queries
```json
{
  "query": "Show all invoices for customer Globex Inc"
}
```

```json
{
  "query": "Count invoices for billing account 'acme west'",
  "count_only": true
}
```

### 4. Amount-Related Queries
```json
{
  "query": "List invoices with amount greater than 1000"
}
```

```json
{
  "query": "Show invoices in EUR currency"
}
```

### 5. Combined Filter Queries
```json
{
  "query": "Show invoices for Acme Corp in USD during 2023"
}
```

```json
{
  "query": "Count invoices for Globex Inc in EUR between Feb 2023 and Apr 2023",
  "count_only": true
}
```

### 6. Edge Cases
```json
{
  "query": "Find invoices for non-existent customer",
  "count_only": false
}
```

```json
{
  "query": "Show invoices from invalid date range",
  "count_only": false
}
```

### 7. Health Check
```json
{}
```

### Sample cURL Commands:

1. For count query:
```bash
curl -X POST http://localhost:8000/query \
-H "Content-Type: application/json" \
-d '{"query":"How many invoices for Acme Corp in 2023?","count_only":true}'
```

2. For detailed query:
```bash
curl -X POST http://localhost:8000/query \
-H "Content-Type: application/json" \
-d '{"query":"Show all invoices for Globex Inc in EUR"}'
```

3. For health check:
```bash
curl -X GET http://localhost:8000/health
```

These prompts cover all the functionality of your MockAPI including:
- Count vs detail responses
- Date filtering
- Customer filtering
- Amount/currency filtering
- Combined filters
- Edge cases
- System health checks

The responses will either return:
- A count with summary (when count_only=true)
- A detailed table of invoices (when count_only=false or omitted)
- "No matching invoices found" when filters don't match any records
- Error messages for invalid requests