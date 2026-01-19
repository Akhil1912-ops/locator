# Google Maps API Setup Guide

To enable location search (autocomplete) when adding stops, you need to set up a Google Maps API key.

## Steps to Get API Key:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create or Select a Project**
   - Click on the project dropdown at the top
   - Create a new project or select an existing one

3. **Enable Required APIs**
   - Go to "APIs & Services" > "Library"
   - Search for and enable:
     - **Places API** (for autocomplete)
     - **Maps JavaScript API** (for map features)

4. **Create API Key**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the generated API key

5. **Configure in Admin Panel**
   - Open `admin/index.html`
   - Find the line: `const GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY_HERE';`
   - Replace `YOUR_GOOGLE_MAPS_API_KEY_HERE` with your actual API key
   - Save the file

## Optional: Restrict API Key (Recommended for Production)

For security, restrict your API key:
- Go to "APIs & Services" > "Credentials"
- Click on your API key
- Under "API restrictions", select "Restrict key"
- Choose "Places API" and "Maps JavaScript API"
- Under "Application restrictions", you can restrict by HTTP referrer (for web)

## Cost Information

- Google Maps offers **$200 free credit per month**
- Places Autocomplete: **$2.83 per 1000 requests** (after free tier)
- For small-scale use, this should be well within the free tier

## Testing

After adding your API key:
1. Open the admin panel
2. Click "Add Bus" or "Route" > "Add Stop"
3. In the "Search Location" field, start typing a location name
4. You should see autocomplete suggestions
5. Select a location - coordinates will be filled automatically

## Troubleshooting

- **"API key not configured" error**: Make sure you replaced the placeholder in `admin/index.html`
- **No autocomplete suggestions**: Check that Places API is enabled in Google Cloud Console
- **"Google Maps API not loaded"**: Verify your API key is correct and Maps JavaScript API is enabled
