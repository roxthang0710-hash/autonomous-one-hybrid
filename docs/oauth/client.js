"use strict";
const SUPABASE = "https://gjdvdohylvsauphhkutw.supabase.co";
const PUBLISHABLE_KEY = "sb_publishable_sJxwXdpQPn4FrrGZPusJmA_Xy5TI0-H";
const API = SUPABASE + "/functions/v1/threads-oauth/start";
const params = new URLSearchParams(location.search);
const outcome = params.get("status");
if (outcome === "connected") document.querySelector("#connected").hidden = false;
if (outcome === "failed") document.querySelector("#failed").hidden = false;
if (outcome) history.replaceState(null, "", location.pathname);
const $ = id => document.getElementById(id);
$("connect").addEventListener("submit", async event => {
  event.preventDefault();
  const button = $("submit"), status = $("status");
  button.disabled = true;
  status.textContent = "Đang xác thực quyền quản trị…";
  try {
    const email = $("email").value.trim();
    const password = $("password").value;
    const login = await fetch(SUPABASE + "/auth/v1/token?grant_type=password", {
      method: "POST", mode: "cors", cache: "no-store", credentials: "omit",
      headers: { "apikey": PUBLISHABLE_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    $("password").value = "";
    if (!login.ok) throw new Error("Không thể đăng nhập Supabase Auth. Kiểm tra tài khoản quản trị Autonomous One.");
    const session = await login.json();
    const response = await fetch(API, {
      method: "POST", mode: "cors", cache: "no-store", credentials: "omit",
      headers: { "Authorization": "Bearer " + session.access_token,
                 "apikey": PUBLISHABLE_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({
        appId: $("appId").value.trim(),
        appSecret: $("appSecret").value,
        enableReplies: $("replies").checked
      })
    });
    $("appSecret").value = "";
    const result = await response.json();
    if (!response.ok || typeof result.authorizeUrl !== "string")
      throw new Error(result.error || "Không tạo được phiên cấp quyền Meta.");
    if (!result.authorizeUrl.startsWith("https://threads.net/oauth/authorize?"))
      throw new Error("Địa chỉ chuyển hướng Meta không hợp lệ.");
    status.style.color = "#176b47";
    status.textContent = "Đã xác thực; chuyển đến Meta để chấp thuận quyền…";
    location.assign(result.authorizeUrl);
  } catch (error) {
    $("password").value = "";
    $("appSecret").value = "";
    status.textContent = error instanceof Error ? error.message : "Đã xảy ra lỗi kết nối.";
    button.disabled = false;
  }
});
