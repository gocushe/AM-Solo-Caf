const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type UserSummary = {
  id: number;
  name: string;
  student_number: string | null;
  username: string | null;
  roles: string[];
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: UserSummary;
};

export type MealInfo = {
  id: number;
  meal_type: "Breakfast" | "Lunch" | "Supper" | "Snack";
  title: string | null;
  is_signup_allowed: boolean;
};

export type DayMeals = {
  date: string;
  is_open: boolean;
  meals: MealInfo[];
};

export type DashboardResponse = {
  user: UserSummary;
  lunches_remaining: number;
  suppers_remaining: number;
  days: DayMeals[];
};

export type SignupItem = {
  signup_id: number;
  meal_id: number;
  meal_type: "Breakfast" | "Lunch" | "Supper" | "Snack";
  date: string;
  signed_up_at: string;
};

export async function apiRequest<T>(
  path: string,
  options?: RequestInit,
  token?: string,
): Promise<T> {
  const headers = new Headers(options?.headers);
  if (!headers.has("Content-Type") && options?.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export { API_BASE_URL };
