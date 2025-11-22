# Mail Writer Cloud Run Service

A Flask application that uses an AI agent to generate personalized email subjects and bodies based on contact information and company website.

## Features

- **AI-powered mail generation**: Uses Claude GPT-4 with web search capabilities
- **Personalized content**: Takes contact name and website as input
- **JSON API**: Simple REST API for easy integration
- **Web search integration**: Agent can search the web for company information
- **Cloud Run ready**: Configured for deployment on Google Cloud Run

## API Endpoints

### POST `/`
Generates an email subject and body for a given contact.

**Request body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "website": "https://www.example.com"
}
```

**Response (success):**
```json
{
  "status": "ok",
  "data": {
    "subject": "Partnership opportunity with Example Inc.",
    "body": "Dear John,\n\nI hope this email finds you well..."
  }
}
```

**Response (error):**
```json
{
  "status": "error",
  "error": "Error message describing what went wrong"
}
```

### GET `/health`
Health check endpoint to verify the service is running.

**Response:**
```json
{
  "status": "healthy"
}
```

## Configuration

### Required Files
- `instructions_prospector.txt` - System instructions for the AI agent
- `prompt_prospector.txt` - Prompt template with placeholders `{contact_name}` and `{website}`

### Prompt Template Variables
The `prompt_prospector.txt` file can contain these placeholders that will be replaced:
- `{contact_name}` - Will be replaced with "FirstName LastName"
- `{website}` - Will be replaced with the company website URL

**Example prompt template:**
```
You are an expert email copywriter. Generate a professional and personalized email 
for the following person: {contact_name} from the company at {website}.

The email should:
1. Be concise and engaging
2. Mention specific details from their company website
3. Have a clear call-to-action

Return as JSON with "subject" and "body" fields.
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure you have the required files:
# - instructions_prospector.txt
# - prompt_prospector.txt

# Run the Flask app
python app.py
```

The app will be available at `http://localhost:8080`

## Deployment on Cloud Run

```bash
gcloud run deploy mail-writer \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300
```

## Testing

### Test with curl
```bash
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Marie",
    "last_name": "Durand",
    "website": "https://www.acme.com"
  }'
```

### Expected output
```json
{
  "status": "ok",
  "data": {
    "subject": "Strategic partnership opportunity for ACME",
    "body": "Dear Marie,\n\nI hope this message finds you well. I've been impressed by ACME's innovative approach to..."
  }
}
```

## Troubleshooting

### Import errors
Make sure all dependencies are installed: `pip install -r requirements.txt`

### File not found errors
Ensure `instructions_prospector.txt` and `prompt_prospector.txt` are in the same directory as `app.py`

### Timeout errors
The AI agent may take time to generate content. The default Cloud Run timeout is set to 300 seconds. 
If you need more time, increase the `--timeout` parameter in the deployment command.

### Agent errors
Check that:
1. The prompt template is valid
2. Variables `{contact_name}` and `{website}` are properly formatted
3. The agent has valid API credentials for web search

## Logging

All operations are logged with prefixes:
- `[DEBUG]` - Debug information
- `[ERROR]` - Error messages

## License

Proprietary - Light and Shutter
