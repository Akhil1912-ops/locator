import axios from 'axios';

// Default backend URL (can be overridden at runtime)
const DEFAULT_API_BASE_URL = __DEV__
    ? 'http://10.61.199.218:8000'  // Your computer's IP address (change if your IP changes)
    : 'https://your-production-url.com';  // For production

const normalizeBaseUrl = (url) => {
    if (!url) return '';
    let normalized = url.trim();
    if (!/^https?:\/\//i.test(normalized)) {
        normalized = `http://${normalized}`;
    }
    return normalized.replace(/\/+$/, '');
};

const api = axios.create({
    baseURL: DEFAULT_API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const setApiBaseUrl = (url) => {
    const normalized = normalizeBaseUrl(url);
    api.defaults.baseURL = normalized || DEFAULT_API_BASE_URL;
};

export const getApiBaseUrl = () => api.defaults.baseURL;

export const loginDriver = async (busNumber, password) => {
    try {
        const response = await api.post('/auth/driver/login', {
            bus_number: busNumber,
            password: password,
        });
        return response.data;
    } catch (error) {
        if (error.response) {
            throw new Error(error.response.data.detail || 'Login failed');
        }
        throw new Error('Network error. Please check your connection.');
    }
};

export const sendLocation = async (sessionToken, latitude, longitude) => {
    try {
        const now = new Date().toISOString();
        const response = await api.post(
            '/driver/location',
            {
                latitude: latitude,
                longitude: longitude,
                recorded_at: now,
            },
            {
                headers: {
                    'X-Session-Token': sessionToken,
                },
            }
        );
        return response.data;
    } catch (error) {
        if (error.response) {
            console.error('Location send error:', error.response.data);
        } else {
            console.error('Network error sending location:', error.message);
        }
        throw error;
    }
};

export const updateDelay = async (sessionToken, delayMinutes, currentStop, nextStop) => {
    try {
        const response = await api.post(
            '/driver/delay',
            {
                delay_minutes: delayMinutes,
                current_stop: currentStop,
                next_stop: nextStop,
            },
            {
                headers: {
                    'X-Session-Token': sessionToken,
                },
            }
        );
        return response.data;
    } catch (error) {
        console.error('Delay update error:', error);
        throw error;
    }
};

