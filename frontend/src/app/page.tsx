"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  apiRequest,
  API_BASE_URL,
  AuthResponse,
  DashboardResponse,
  DayMeals,
  MealInfo,
  SignupItem,
  UserSummary,
} from "@/lib/api";

type MealType = "Breakfast" | "Lunch" | "Supper" | "Snack";

const mealTimes: MealType[] = ["Breakfast", "Lunch", "Supper", "Snack"];

function monthGrid(year: number, monthIndex: number) {
  const firstDay = new Date(year, monthIndex, 1).getDay();
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const cells: Array<number | null> = [];

  for (let i = 0; i < firstDay; i += 1) cells.push(null);
  for (let day = 1; day <= daysInMonth; day += 1) cells.push(day);
  while (cells.length % 7 !== 0) cells.push(null);

  return cells;
}

export default function Home() {
  const now = new Date();
  const year = now.getFullYear();
  const monthIndex = now.getMonth();

  const [view, setView] = useState<"login" | "dashboard">("login");
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [token, setToken] = useState<string>("");
  const [user, setUser] = useState<UserSummary | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [signups, setSignups] = useState<SignupItem[]>([]);

  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerStudentNumber, setRegisterStudentNumber] = useState("");
  const [registerLastName, setRegisterLastName] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [showMealHistory, setShowMealHistory] = useState(false);
  const calendarCells = useMemo(() => monthGrid(year, monthIndex), [monthIndex, year]);

  useEffect(() => {
    const saved = localStorage.getItem("cmu_token");
    if (!saved) {
      return;
    }
    setToken(saved);
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }

    const run = async () => {
      try {
        const me = await apiRequest<UserSummary>("/auth/me", { method: "GET" }, token);
        setUser(me);
        setView("dashboard");
      } catch {
        localStorage.removeItem("cmu_token");
        setToken("");
      }
    };

    void run();
  }, [token]);

  useEffect(() => {
    if (!token || view !== "dashboard") {
      return;
    }

    const loadDashboard = async () => {
      try {
        const data = await apiRequest<DashboardResponse>(
          `/me/dashboard?year=${year}&month=${monthIndex + 1}`,
          { method: "GET" },
          token,
        );
        const signupData = await apiRequest<SignupItem[]>("/me/signups", { method: "GET" }, token);
        setDashboard(data);
        setUser(data.user);
        setSignups(signupData);
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Could not load dashboard");
      }
    };

    void loadDashboard();
  }, [monthIndex, token, view, year]);

  const selectedDayDate = selectedDay
    ? `${year}-${String(monthIndex + 1).padStart(2, "0")}-${String(selectedDay).padStart(2, "0")}`
    : "";
  const selectedDayMeals: MealInfo[] =
    (dashboard?.days.find((d: DayMeals) => d.date === selectedDayDate)?.meals ?? []).sort((a, b) => {
      return mealTimes.indexOf(a.meal_type) - mealTimes.indexOf(b.meal_type);
    });

  const sortedMeals = [...signups].sort((a, b) => a.date.localeCompare(b.date));

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const data = await apiRequest<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username: loginUsername, password: loginPassword, admin_login: isAdminLogin }),
      });
      localStorage.setItem("cmu_token", data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      setView("dashboard");
      setLoginPassword("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const data = await apiRequest<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          student_number: registerStudentNumber,
          last_name: registerLastName,
          password: registerPassword,
        }),
      });
      localStorage.setItem("cmu_token", data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      setShowRegister(false);
      setView("dashboard");
      setRegisterPassword("");
      setRegisterLastName("");
      setRegisterStudentNumber("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("cmu_token");
    setToken("");
    setUser(null);
    setDashboard(null);
    setSignups([]);
    setView("login");
  };

  const signUpForMeal = async (mealId: number) => {
    if (!token) return;
    setMessage("");
    try {
      await apiRequest<SignupItem>(
        "/me/signups",
        {
          method: "POST",
          body: JSON.stringify({ meal_id: mealId }),
        },
        token,
      );

      const data = await apiRequest<DashboardResponse>(
        `/me/dashboard?year=${year}&month=${monthIndex + 1}`,
        { method: "GET" },
        token,
      );
      const signupData = await apiRequest<SignupItem[]>("/me/signups", { method: "GET" }, token);
      setDashboard(data);
      setSignups(signupData);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to sign up for meal");
    }
  };

  const deleteSignup = async (signupId: number) => {
    if (!token) return;
    setMessage("");
    try {
      await apiRequest<{ message: string }>(`/me/signups/${signupId}`, { method: "DELETE" }, token);
      const data = await apiRequest<DashboardResponse>(
        `/me/dashboard?year=${year}&month=${monthIndex + 1}`,
        { method: "GET" },
        token,
      );
      const signupData = await apiRequest<SignupItem[]>("/me/signups", { method: "GET" }, token);
      setDashboard(data);
      setSignups(signupData);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to delete signup");
    }
  };

  const changePassword = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setLoading(true);
    setMessage("");

    try {
      await apiRequest<{ message: string }>(
        "/auth/change-password",
        {
          method: "POST",
          body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
        },
        token,
      );
      setMessage("Password updated successfully");
      setOldPassword("");
      setNewPassword("");
      setShowSettings(false);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update password");
    } finally {
      setLoading(false);
    }
  };

  if (view === "login") {
    return (
      <main className="min-h-screen">
        <div className="absolute left-6 top-6 z-10 rounded-full bg-white/85 px-3 py-1 text-xs font-semibold text-[#356756] shadow">
          API: {API_BASE_URL}
        </div>
        <button
          type="button"
          onClick={() => setIsAdminLogin((prev) => !prev)}
          className="absolute right-6 top-6 z-10 rounded-full border border-[#0f4f3f]/40 bg-white/90 px-4 py-2 text-sm font-semibold text-[#0f4f3f] shadow-[0_6px_16px_rgba(0,0,0,0.12)]"
        >
          {isAdminLogin ? "Student" : "Admin"}
        </button>
        <section className="relative min-h-screen w-full overflow-hidden px-6 py-12 sm:px-8">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_15%,#fef8d7_0%,#fef8d7_25%,transparent_60%),radial-gradient(circle_at_80%_75%,#a9d2be_0%,#a9d2be_18%,transparent_50%),linear-gradient(145deg,#e8f3ec_0%,#f6f9d9_45%,#fffef5_100%)]" />
          <div className="relative mx-auto mt-14 w-full max-w-md rounded-3xl border border-[#1d6b53]/20 bg-white/95 p-8 shadow-[0_28px_50px_rgba(15,79,63,0.2)]">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#1d6b53]">CMU Cafeteria</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-[#0a2f25]">
              {isAdminLogin ? "Admin Sign In" : "Student Sign In"}
            </h1>
            <p className="mt-2 text-sm text-[#245645]">
              {isAdminLogin ? "Use your admin credentials." : "Use Student Number + password."}
            </p>

            <form onSubmit={handleLogin} className="mt-8 space-y-4">
              <label className="block text-sm font-medium text-[#184a3a]">
                {isAdminLogin ? "Username" : "Student Number"}
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  placeholder={isAdminLogin ? "admin" : "e.g. 123"}
                  className="mt-2 w-full rounded-2xl border border-[#d3decf] bg-[#fcfdf8] px-4 py-3 text-[#0e2f25] outline-none ring-[#f7b500] transition focus:ring-2"
                />
              </label>
              <label className="block text-sm font-medium text-[#184a3a]">
                Password
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder={isAdminLogin ? "admin" : "Last name or custom password"}
                  className="mt-2 w-full rounded-2xl border border-[#d3decf] bg-[#fcfdf8] px-4 py-3 text-[#0e2f25] outline-none ring-[#f7b500] transition focus:ring-2"
                />
              </label>
              <button
                type="submit"
                disabled={loading}
                className="mt-3 w-full rounded-2xl bg-[#f7b500] px-4 py-3 font-bold text-[#143326] shadow-[0_8px_18px_rgba(247,181,0,0.3)] transition hover:-translate-y-0.5 disabled:opacity-60"
              >
                {loading ? "Signing In..." : "Sign In"}
              </button>
            </form>

            {!isAdminLogin && (
              <p className="mt-6 text-center text-sm text-[#305e4f]">
                New student?{" "}
                <button
                  type="button"
                  onClick={() => setShowRegister(true)}
                  className="font-semibold text-[#0f4f3f] underline underline-offset-4"
                >
                  Register account
                </button>
              </p>
            )}

            {message && <p className="mt-4 text-sm font-semibold text-[#8f2c1d]">{message}</p>}
          </div>
        </section>

        {showRegister && (
          <div className="fixed inset-0 z-20 flex items-center justify-center bg-[#0a2f25]/40 p-4">
            <form onSubmit={handleRegister} className="w-full max-w-md rounded-3xl bg-white p-6 shadow-[0_28px_50px_rgba(0,0,0,0.3)]">
              <h2 className="text-xl font-bold text-[#12382e]">Student Registration</h2>
              <div className="mt-4 space-y-3">
                <input
                  value={registerStudentNumber}
                  onChange={(e) => setRegisterStudentNumber(e.target.value)}
                  placeholder="Student Number"
                  className="w-full rounded-2xl border border-[#d3decf] px-4 py-3"
                />
                <input
                  value={registerLastName}
                  onChange={(e) => setRegisterLastName(e.target.value)}
                  placeholder="Last Name"
                  className="w-full rounded-2xl border border-[#d3decf] px-4 py-3"
                />
                <input
                  type="password"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full rounded-2xl border border-[#d3decf] px-4 py-3"
                />
              </div>
              <div className="mt-4 flex gap-3">
                <button type="submit" className="rounded-2xl bg-[#f7b500] px-4 py-2 font-semibold text-[#143326]">
                  Register
                </button>
                <button
                  type="button"
                  onClick={() => setShowRegister(false)}
                  className="rounded-2xl bg-[#ebf4ef] px-4 py-2 font-semibold text-[#0f4f3f]"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#f4f8ed_0%,#f6f8e6_38%,#f4f7ef_100%)] px-4 py-5 sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-5 rounded-3xl border border-[#2b7a62]/15 bg-white/95 px-5 py-4 shadow-[0_18px_32px_rgba(0,0,0,0.14)] sm:px-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="text-2xl font-bold text-[#0f4f3f] sm:text-3xl">CMU Cafeteria</h1>
            <button
              type="button"
              onClick={() => setShowMealHistory(true)}
              className="rounded-full border border-[#0f4f3f]/20 bg-[#ebf4ef] px-4 py-2 text-sm font-semibold text-[#0f4f3f]"
            >
              {user?.name ?? "Student"}
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <div className="rounded-2xl bg-[#f7b500]/15 px-4 py-3 text-sm font-semibold text-[#573b00]">
              Lunches: {dashboard?.lunches_remaining ?? 0}
            </div>
            <div className="rounded-2xl bg-[#0f4f3f]/12 px-4 py-3 text-sm font-semibold text-[#0f4f3f]">
              Suppers: {dashboard?.suppers_remaining ?? 0}
            </div>
            <button
              type="button"
              onClick={() => setShowSettings(true)}
              className="rounded-2xl bg-[#0f4f3f] px-4 py-3 text-sm font-semibold text-white"
            >
              Settings
            </button>
            <button
              type="button"
              onClick={logout}
              className="rounded-2xl bg-[#114235] px-4 py-3 text-sm font-semibold text-white"
            >
              Logout
            </button>
          </div>
          {message && <p className="mt-3 text-sm font-semibold text-[#8f2c1d]">{message}</p>}
        </header>

        <section className="rounded-3xl border border-[#2b7a62]/15 bg-white p-5 shadow-[0_20px_35px_rgba(0,0,0,0.13)] sm:p-8">
          <div className="mb-4 flex items-end justify-between">
            <h2 className="text-xl font-bold text-[#163a2f] sm:text-2xl">
              {new Date(year, monthIndex, 1).toLocaleString(undefined, { month: "long", year: "numeric" })}
            </h2>
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-[#2f6653]">Material-style Monthly Planner</p>
          </div>
          <div className="grid grid-cols-7 gap-2 text-center text-xs font-bold uppercase tracking-[0.1em] text-[#4b6d61] sm:gap-3 sm:text-sm">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((label) => (
              <div key={label}>{label}</div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-7 gap-2 sm:gap-3">
            {calendarCells.map((day, idx) => {
              if (!day) {
                return <div key={`empty-${idx}`} className="h-16 rounded-2xl bg-[#f6f8f4] sm:h-24" />;
              }

              const date = new Date(year, monthIndex, day);
              const isPast = date < new Date(now.getFullYear(), now.getMonth(), now.getDate());
              const isToday = day === now.getDate();

              return (
                <button
                  key={day}
                  type="button"
                  disabled={isPast}
                  onClick={() => setSelectedDay(day)}
                  className={`h-16 rounded-2xl border p-2 text-left transition sm:h-24 ${
                    isPast
                      ? "cursor-not-allowed border-[#dde5dc] bg-[#ebefea] text-[#9aab9f]"
                      : "border-[#d6e3d8] bg-[#fafdff] text-[#205343] shadow-[0_6px_14px_rgba(20,60,48,0.08)] hover:-translate-y-0.5"
                  } ${isToday ? "ring-2 ring-[#f7b500]" : ""}`}
                >
                  <span className="text-sm font-bold sm:text-lg">{day}</span>
                </button>
              );
            })}
          </div>
        </section>
      </div>

      {selectedDay && (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-[#0a2f25]/45 p-4">
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-[0_28px_50px_rgba(0,0,0,0.3)]">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-[#12382e]">
                Meals for {new Date(year, monthIndex, selectedDay).toLocaleDateString()}
              </h3>
              <button type="button" onClick={() => setSelectedDay(null)} className="rounded-full bg-[#edf2ee] px-3 py-1 text-sm">
                Close
              </button>
            </div>
            <div className="space-y-3">
              {selectedDayMeals.length === 0 && (
                <p className="rounded-2xl border border-[#dce8df] bg-[#fbfdf9] px-4 py-3 text-sm text-[#4e695f]">
                  No menu loaded for this day yet.
                </p>
              )}
              {selectedDayMeals.map((meal) => (
                <div
                  key={meal.id}
                  className="flex items-center justify-between rounded-2xl border border-[#dce8df] bg-[#fbfdf9] px-4 py-3"
                >
                  <p className="font-semibold text-[#194e3d]">{meal.meal_type}</p>
                  {meal.meal_type === "Snack" || !meal.is_signup_allowed ? (
                    <span className="rounded-full bg-[#e8ece8] px-3 py-1 text-xs font-semibold text-[#63786f]">View only</span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => signUpForMeal(meal.id)}
                      className="rounded-full bg-[#f7b500] px-4 py-2 text-xs font-bold text-[#163728]"
                    >
                      Sign Up
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {showMealHistory && (
        <div className="fixed inset-0 z-40 flex justify-end bg-[#0a2f25]/30">
          <div className="h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-[0_20px_40px_rgba(0,0,0,0.35)]">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="text-xl font-bold text-[#153c30]">Signed-up Meals</h3>
              <button type="button" onClick={() => setShowMealHistory(false)} className="rounded-full bg-[#edf2ee] px-3 py-1 text-sm">
                Close
              </button>
            </div>

            <div className="space-y-3">
              {sortedMeals.length === 0 && <p className="text-sm text-[#4e695f]">No meals signed up yet.</p>}
              {sortedMeals.map((item) => (
                <div
                  key={item.signup_id}
                  className="flex items-center justify-between rounded-2xl border border-[#d8e4da] bg-[#f8fbf8] px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-semibold text-[#174534]">{item.date}</p>
                    <p className="text-xs text-[#3f685a]">{item.meal_type}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => deleteSignup(item.signup_id)}
                    className="rounded-full bg-[#ffe4dd] px-3 py-1 text-xs font-semibold text-[#8f2c1d]"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0a2f25]/45 p-4">
          <form onSubmit={changePassword} className="w-full max-w-md rounded-3xl bg-white p-6 shadow-[0_28px_50px_rgba(0,0,0,0.3)]">
            <h3 className="text-xl font-bold text-[#153c30]">Change Password</h3>
            <p className="mt-1 text-sm text-[#46675d]">Available for both students and admins.</p>
            <div className="mt-4 space-y-3">
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                placeholder="Old password"
                className="w-full rounded-2xl border border-[#d3decf] px-4 py-3"
              />
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="New password"
                className="w-full rounded-2xl border border-[#d3decf] px-4 py-3"
              />
            </div>
            <div className="mt-4 flex gap-3">
              <button
                type="submit"
                className="rounded-2xl bg-[#f7b500] px-4 py-2 font-semibold text-[#143326] disabled:opacity-60"
                disabled={loading}
              >
                Update
              </button>
              <button
                type="button"
                onClick={() => setShowSettings(false)}
                className="rounded-2xl bg-[#ebf4ef] px-4 py-2 font-semibold text-[#0f4f3f]"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  );
}
