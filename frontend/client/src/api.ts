const API_URL = "http://127.0.0.1:8000";
const API = {
    login: `${API_URL}/api/auth/login`,
    register: `${API_URL}/api/auth/register`,
    profile: (usn: string) => `${API_URL}/api/profiles/${usn}`,
    updateProfile: (studentId: string) => `${API_URL}/api/profiles/${studentId}`,
    posts: `${API_URL}/api/posts/`,
    resources: `${API_URL}/api/resources/upload`,
};

export async function apiFetch(
    endpoint: string,
    options: RequestInit = {}
) {
    const token = localStorage.getItem("access_token");

    const headers = new Headers(options.headers);

    if (!(options.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
    }

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const errorText = await response.text();

        let errorMessage = `API error: ${response.status}`;

        try {
            const errorData = JSON.parse(errorText);

            if (typeof errorData.detail === "string") {
                errorMessage = errorData.detail;
            } else if (errorData.detail) {
                errorMessage = JSON.stringify(errorData.detail);
            }
        } catch {
            if (errorText) {
                errorMessage = errorText;
            }
        }

        throw new Error(errorMessage);
    }

    return response.json();
}