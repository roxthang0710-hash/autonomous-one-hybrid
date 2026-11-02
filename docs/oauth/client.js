"use strict";
// Passwordless owner authorization. Auth JWT is held in memory only,
// never copied to GitHub, localStorage, a URL query, or Supabase tables.
const SUPABASE = "https://gjdvdohylvsauphhkutw.supabase.co";
const PUBLISHABLE_KEY = "sb_publishable_sJxwXdpQPn4FrrGZPusJmA_Xy5TI0-H";
const API_ROOT = SUPABASE + "/functions/v1/threads-oauth";
const AUTH_ROOT = SUPABASE + "/auth/v1";
const RETURN_URL = location.origin + location.pathname;
const $ = id => document.getElementById(id);
let ownerAccessToken = null;

// Retain an owner-verified login only within this browser tab, with a short
// timeout. A Meta OAuth error redirects back to this tab. Never request a new
// email merely because Meta denied/failed a code exchange.
const OWNER_SESSION_KEY = "ao_threads_verified_owner_session_v1";
const MAX_SESSION_AGE_MS = 25 * 60 * 1000;
function forgetOwnerSession() {
  ownerAccessToken = null;
  try { sessionStorage.removeItem(OWNER_SESSION_KEY); } catch (_) {}
}
function cacheOwnerSession(token) {
  ownerAccessToken = token;
  try {
    sessionStorage.setItem(OWNER_SESSION_KEY,
      JSON.stringify({ accessToken: token, savedAt: Date.now() }));
  } catch (_) {
    // Browser may block sessionStorage; email login still works this tab
    // until navigating to Meta.
  }
}
async function recoverOwnerSession() {
  if (outcome === "connected") {
    forgetOwnerSession();
    return;
  }
  let stored;
  try {
    stored = JSON.parse(sessionStorage.getItem(OWNER_SESSION_KEY) || "null");
  } catch (_) {
    forgetOwnerSession();
    return;
  }
  if (!stored || typeof stored.accessToken !== "string" ||
      !Number.isFinite(stored.savedAt) ||
      stored.savedAt > Date.now() ||
      Date.now() - stored.savedAt > MAX_SESSION_AGE_MS) {
    forgetOwnerSession();
    return;
  }
  try {
    await verifyOwner(stored.accessToken);
    // Preserve the original timestamp; reloading cannot extend the limit.
    ownerAccessToken = stored.accessToken;
    showMeta();
  } catch (_) {
    forgetOwnerSession();
    showLoginError("Phiên quản trị đã hết hạn. Khi giới hạn gửi email được gỡ, bạn có thể yêu cầu liên kết đăng nhập mới.");
  }
}

const params = new URLSearchParams(location.search);
const outcome = params.get("status");
const failureReason = params.get("reason");
const FAILURE_MESSAGES = Object.freeze({
  meta_denied: "Meta chưa chấp thuận quyền cho ứng dụng hoặc bạn đã hủy xác nhận.",
  invalid_request: "Yêu cầu cấp quyền không hợp lệ. Hãy bắt đầu lại từ biểu mẫu.",
  expired_session: "Phiên cấp quyền đã hết hạn hoặc mã đã được sử dụng. Hãy đăng nhập lại và cấp quyền mới.",
  code_exchange: "Meta đã xác nhận quyền nhưng không đổi được mã thành token ngắn hạn. Hãy kiểm tra đúng Threads App ID, Threads App Secret và callback URI.",
  long_token: "Đã nhận token ngắn hạn nhưng không đổi được token dài hạn. Hãy kiểm tra quyền ứng dụng và Threads API.",
  account_verify: "Đã nhận token nhưng không xác minh được tài khoản Threads. Hãy kiểm tra quyền threads_basic.",
  wrong_account: "Bạn đã cấp quyền cho tài khoản Threads khác, không phải @dohay_dilam.",
  vault_save: "Meta đã cấp token nhưng máy chủ chưa lưu được token vào kho bảo mật. Cần kiểm tra cấu hình Supabase.",
  unknown: "Kết nối chưa hoàn tất. Vui lòng bắt đầu một phiên cấp quyền mới.",
});
if (outcome === "connected") $("connected").hidden = false;
if (outcome === "failed") {
  const box = $("failed");
  box.hidden = false;
  // Only render fixed client-authored messages, never untrusted URL strings.
  box.textContent = FAILURE_MESSAGES[failureReason] || FAILURE_MESSAGES.unknown;
}
if (outcome) history.replaceState(null, "", RETURN_URL);

function showLoginError(message) {
  $("login-status").textContent = message;
  $("login-status").style.color = "#ab4135";
}
function showMeta() {
  $("login-section").hidden = true;
  $("meta-section").hidden = false;
}
async function verifyOwner(token) {
  const response = await fetch(API_ROOT + "/whoami", {
    method: "GET", credentials: "omit", cache: "no-store", mode: "cors",
    headers: { Authorization: "Bearer " + token, apikey: PUBLISHABLE_KEY }
  });
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error("Email này chưa có quyền quản trị Autonomous One. Vui lòng sử dụng đúng tài khoản đã được cấp quyền.");
    }
    throw new Error("Không kiểm tra được quyền quản trị. Hãy thử lại sau.");
  }
  const data = await response.json();
  if (data.authorized !== true) throw new Error("Không đủ quyền quản trị.");
}

// Supabase Email Magic Link implicit flow returns access_token in the URL
// fragment. Immediately scrub it from address bar/history before network use.
async function consumeEmailMagicLink() {
  if (!location.hash) return;
  const hash = new URLSearchParams(location.hash.slice(1));
  const accessToken = hash.get("access_token");
  const type = hash.get("token_type");
  const error = hash.get("error");
  history.replaceState(null, "", RETURN_URL);
  if (error) {
    showLoginError("Liên kết xác thực đã hết hạn hoặc không hợp lệ. Hãy gửi lại một liên kết mới.");
    return;
  }
  if (!accessToken || type?.toLowerCase() !== "bearer") return;
  $("login-status").textContent = "Đang xác minh chủ sở hữu…";
  try {
    await verifyOwner(accessToken);
    cacheOwnerSession(accessToken);
    showMeta();
  } catch (err) {
    forgetOwnerSession();
    showLoginError(err instanceof Error ? err.message : "Xác minh không thành công.");
  }
}

$("login-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = $("send-link");
  button.disabled = true;
  $("login-status").textContent = "Đang gửi liên kết đăng nhập…";
  try {
    const email = $("email").value.trim().toLowerCase();
    // Never create unauthorized users; only existing reviewer email works.
    const response = await fetch(AUTH_ROOT + "/otp?redirect_to=" + encodeURIComponent(RETURN_URL), {
      method: "POST", mode: "cors", cache: "no-store", credentials: "omit",
      headers: { apikey: PUBLISHABLE_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({
        email, create_user: false
      })
    });
    if (response.status === 429) {
      throw new Error("Supabase giới hạn số lần gửi email. Vui lòng thử lại sau.");
    }
    if (!response.ok) {
      throw new Error("Không gửi được liên kết. Hãy kiểm tra email quản trị hoặc cài đặt xác thực của Supabase.");
    }
    $("login-status").style.color = "#176b47";
    $("login-status").textContent =
      "Đã yêu cầu liên kết đăng nhập. Kiểm tra hộp thư và Thư rác của email đã được cấp quyền, sau đó bấm liên kết do Supabase gửi. Đừng chia sẻ liên kết này.";
  } catch (err) {
    showLoginError(err instanceof Error ? err.message : "Có lỗi khi gửi email.");
  } finally {
    button.disabled = false;
  }
});

$("connect").addEventListener("submit", async event => {
  event.preventDefault();
  const button = $("submit"), status = $("status");
  if (!ownerAccessToken) {
    status.textContent = "Phiên đăng nhập không có hiệu lực. Hãy mở liên kết email mới.";
    return;
  }
  button.disabled = true;
  status.textContent = "Đang xác thực quyền và tạo phiên cấp phép Meta…";
  try {
    const response = await fetch(API_ROOT + "/start", {
      method: "POST", mode: "cors", cache: "no-store", credentials: "omit",
      headers: {
        Authorization: "Bearer " + ownerAccessToken,
        apikey: PUBLISHABLE_KEY, "Content-Type": "application/json"
      },
      body: JSON.stringify({
        appId: $("appId").value.trim(),
        appSecret: $("appSecret").value,
        enableReplies: $("replies").checked
      })
    });
    $("appSecret").value = "";
    const data = await response.json();
    if (!response.ok || typeof data.authorizeUrl !== "string") {
      throw new Error(data.error || "Chưa thể khởi tạo cấp quyền Threads.");
    }
    if (!data.authorizeUrl.startsWith("https://threads.net/oauth/authorize?")) {
      throw new Error("Đường dẫn cấp quyền không đúng máy chủ Meta Threads.");
    }
    // Keep the short-lived, owner-verified session in this tab until the
    // OAuth callback succeeds. If Meta returns a failure, the owner can
    // retry without triggering a new email send or bypassing authorization.
    status.style.color = "#176b47";
    status.textContent = "Đang chuyển sang Meta để chấp thuận quyền…";
    location.assign(data.authorizeUrl);
  } catch (err) {
    $("appSecret").value = "";
    status.textContent = err instanceof Error ? err.message : "Kết nối chưa thành công.";
    button.disabled = false;
  }
});

void (async () => {
  if (location.hash) await consumeEmailMagicLink();
  else await recoverOwnerSession();
})();
