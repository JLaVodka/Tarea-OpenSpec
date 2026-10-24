"use strict";

const state = {
  token: sessionStorage.getItem("access_token"),
  user: null,
  spaces: [],
  reservations: [],
  accounts: [],
};

const byId = (id) => document.getElementById(id);
const hasRole = (name) => Boolean(state.user?.roles?.includes(name));
const isSpaceManager = () => hasRole("ADMIN_ESPACIOS");
const isSystemAdmin = () => hasRole("ADMIN_SISTEMA");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function notify(message, isError = false) {
  const notice = byId("notice");
  notice.textContent = message;
  notice.classList.toggle("is-error", isError);
  notice.hidden = false;
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => { notice.hidden = true; }, 5500);
}

function errorMessage(data, fallback) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map((item) => item.msg).join(". ");
  return fallback;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  let response;
  try {
    response = await fetch(path, { ...options, headers });
  } catch (_error) {
    throw new Error("No se pudo conectar con el servidor. Comprueba que la aplicación siga activa.");
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && state.token && path !== "/auth/login") {
      clearSession(false);
      notify("Tu sesión venció. Inicia sesión nuevamente.", true);
    }
    throw new Error(errorMessage(data, `No se pudo completar la operación (${response.status}).`));
  }
  return data;
}

function clearSession(showMessage = true) {
  state.token = null;
  state.user = null;
  state.spaces = [];
  state.reservations = [];
  state.accounts = [];
  sessionStorage.removeItem("access_token");
  byId("auth-view").hidden = false;
  byId("workspace-view").hidden = true;
  byId("session-summary").hidden = true;
  if (showMessage) notify("Sesión cerrada correctamente.");
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Fecha inválida";
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function localDateTimeToIso(value) {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) throw new Error("Completa una fecha y hora válidas.");
  return date.toISOString();
}

function readInterval(form) {
  const startsAt = localDateTimeToIso(form.elements.starts_at.value);
  const endsAt = localDateTimeToIso(form.elements.ends_at.value);
  if (new Date(endsAt) <= new Date(startsAt)) {
    throw new Error("La fecha final debe ser posterior a la fecha inicial.");
  }
  return { starts_at: startsAt, ends_at: endsAt };
}

function showPanel(panelId) {
  document.querySelectorAll(".content-panel").forEach((panel) => {
    panel.hidden = panel.id !== panelId;
  });
  document.querySelectorAll(".nav-link").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.panel === panelId);
  });
}

function reservationStatus(status) {
  const className = `status-${String(status || "").toLowerCase()}`;
  return `<span class="status-pill ${className}">${escapeHtml(status)}</span>`;
}

function renderReservation(reservation, actions = true) {
  const space = state.spaces.find((item) => item.id === reservation.space_id);
  const title = space?.name || `Espacio #${reservation.space_id}`;
  const ownRequest = reservation.requester_id === state.user?.id;
  const buttons = [];
  if (actions && reservation.status === "PENDIENTE" && isSpaceManager()) {
    buttons.push(`<button class="button button-secondary button-small" data-action="approve" data-id="${reservation.id}">Aprobar</button>`);
    buttons.push(`<button class="button button-danger button-small" data-action="reject" data-id="${reservation.id}">Rechazar</button>`);
  }
  const requesterCanCancel = ownRequest && (hasRole("ESTUDIANTE") || hasRole("DOCENTE"));
  if (actions && reservation.status !== "CANCELADA" && reservation.status !== "RECHAZADA" && (requesterCanCancel || isSpaceManager())) {
    buttons.push(`<button class="button button-quiet button-small" data-action="cancel" data-id="${reservation.id}" data-own="${requesterCanCancel}">Cancelar</button>`);
  }
  if (actions) buttons.push(`<button class="button button-quiet button-small" data-action="history" data-id="${reservation.id}">Ver historial</button>`);
  return `<article class="data-card">
    <div class="data-card-top"><div><h3>${escapeHtml(title)}</h3><p>${escapeHtml(formatDate(reservation.starts_at))} — ${escapeHtml(formatDate(reservation.ends_at))}</p><p>Solicitud #${reservation.id}</p></div>${reservationStatus(reservation.status)}</div>
    ${buttons.length ? `<div class="data-card-actions">${buttons.join("")}</div>` : ""}
  </article>`;
}

function renderSpace(space, admin = false) {
  const inactive = !space.is_active;
  const actions = admin ? `<div class="data-card-actions">
    <button class="button button-quiet button-small" data-action="edit-space" data-id="${space.id}">Editar</button>
    <button class="button button-secondary button-small" data-action="toggle-space" data-id="${space.id}" data-active="${space.is_active}">${space.is_active ? "Desactivar" : "Activar"}</button>
    <button class="button button-danger button-small" data-action="delete-space" data-id="${space.id}">Eliminar</button>
  </div>` : "";
  return `<article class="space-card">
    <span class="space-type">${escapeHtml(space.space_type.replaceAll("_", " "))}</span>
    <h3>${escapeHtml(space.name)}</h3>
    <p>⌖ ${escapeHtml(space.location)}</p>
    <p>♧ Capacidad para ${escapeHtml(space.capacity)} personas</p>
    ${inactive ? '<span class="status-pill status-cancelada">Inactivo</span>' : '<span class="status-pill status-aprobada">Disponible para solicitudes</span>'}
    ${actions}
  </article>`;
}

function renderEmpty(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function fillSpaceOptions() {
  const options = state.spaces.filter((space) => space.is_active)
    .map((space) => `<option value="${space.id}">${escapeHtml(space.name)} · ${escapeHtml(space.location)}</option>`)
    .join("");
  const content = options || '<option value="">No hay espacios activos</option>';
  ["availability-space", "reservation-space"].forEach((id) => {
    const select = byId(id);
    const previous = select.value;
    select.innerHTML = content;
    if ([...select.options].some((option) => option.value === previous)) select.value = previous;
    select.disabled = !options;
  });
}

function renderAccounts() {
  byId("accounts-list").innerHTML = state.accounts.length
    ? state.accounts.map((account) => `<article class="data-card">
        <div class="data-card-top"><div><h3>${escapeHtml(account.email)} · #${account.id}</h3><p>Roles: ${escapeHtml(account.roles.join(", ") || "sin rol")}</p></div>${account.is_active ? '<span class="status-pill status-aprobada">Activa</span>' : '<span class="status-pill status-cancelada">Inactiva</span>'}</div>
        <div class="data-card-actions"><button class="button button-quiet button-small" data-action="toggle-account" data-id="${account.id}" data-active="${account.is_active}">${account.is_active ? "Desactivar cuenta" : "Activar cuenta"}</button></div>
      </article>`).join("")
    : renderEmpty("No hay cuentas para mostrar.");
}

function renderApplication() {
  byId("auth-view").hidden = true;
  byId("workspace-view").hidden = false;
  byId("session-summary").hidden = false;
  byId("session-user").textContent = `${state.user.email} · ${state.user.roles.join(", ")}`;
  byId("greeting-name").textContent = state.user.email.split("@")[0];

  const canAdmin = isSpaceManager() || isSystemAdmin();
  byId("admin-nav").hidden = !canAdmin;
  byId("space-admin-section").hidden = !isSpaceManager();
  byId("reservation-admin-section").hidden = !isSpaceManager();
  byId("account-admin-section").hidden = !isSystemAdmin();

  const activeSpaces = state.spaces.filter((space) => space.is_active);
  const ownReservations = state.reservations.filter((item) => item.requester_id === state.user.id);
  byId("space-count").textContent = String(activeSpaces.length);
  byId("reservation-count").textContent = String(ownReservations.length);
  byId("approved-count").textContent = String(ownReservations.filter((item) => item.status === "APROBADA").length);
  byId("spaces-list").innerHTML = activeSpaces.length
    ? activeSpaces.map((space) => renderSpace(space)).join("")
    : renderEmpty("Aún no hay espacios activos. Vuelve a consultar más tarde.");
  byId("admin-spaces-list").innerHTML = state.spaces.length
    ? state.spaces.map((space) => renderSpace(space, true)).join("")
    : renderEmpty("Todavía no hay espacios registrados.");
  byId("reservations-list").innerHTML = state.reservations.length
    ? state.reservations.map((item) => renderReservation(item)).join("")
    : renderEmpty("Aún no tienes solicitudes. Explora los espacios y crea la primera.");
  byId("recent-reservations").innerHTML = ownReservations.length
    ? ownReservations.slice(-3).reverse().map((item) => renderReservation(item, false)).join("")
    : renderEmpty("Tus solicitudes recientes aparecerán aquí.");
  byId("review-list").innerHTML = isSpaceManager()
    ? state.reservations.filter((item) => item.status === "PENDIENTE").map((item) => renderReservation(item)).join("") || renderEmpty("No tienes solicitudes pendientes por revisar.")
    : "";
  renderAccounts();
  fillSpaceOptions();
}

async function refreshApplication() {
  const [spaces, reservations] = await Promise.all([request("/spaces"), request("/reservations")]);
  state.spaces = spaces;
  state.reservations = reservations;
  state.accounts = isSystemAdmin() ? await request("/users") : [];
  renderApplication();
}

async function startSession(token, user) {
  state.token = token;
  state.user = user;
  sessionStorage.setItem("access_token", token);
  await refreshApplication();
  showPanel("overview-panel");
}

async function handleLogin(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget));
  try {
    const result = await request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
    await startSession(result.access_token, result.user);
    event.currentTarget.reset();
    notify("Sesión iniciada. Ya puedes gestionar tus espacios.");
  } catch (error) {
    notify(error.message, true);
  }
}

async function handleRegistration(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget));
  try {
    const user = await request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
    byId("login-email").value = user.email;
    byId("login-password").focus();
    event.currentTarget.reset();
    event.currentTarget.closest("details").open = false;
    notify("Cuenta de estudiante creada. Inicia sesión para continuar.");
  } catch (error) {
    notify(error.message, true);
  }
}

function bindForm(id, handler) {
  byId(id).addEventListener("submit", async (event) => {
    const button = event.currentTarget.querySelector('button[type="submit"]');
    const originalLabel = button.innerHTML;
    button.disabled = true;
    button.textContent = "Procesando…";
    try { await handler(event); } finally {
      button.innerHTML = originalLabel;
      button.disabled = false;
    }
  });
}

bindForm("login-form", handleLogin);
bindForm("register-form", handleRegistration);

bindForm("availability-form", async (event) => {
  const form = event.currentTarget;
  try {
    const interval = readInterval(form);
    const query = new URLSearchParams({ space_id: form.elements.space_id.value, ...interval });
    const result = await request(`/availability?${query}`);
    const output = byId("availability-result");
    output.hidden = false;
    output.classList.toggle("is-busy", !result.active || !result.available);
    output.textContent = !result.active ? "Este espacio está inactivo y no se puede reservar."
      : result.available ? "¡El espacio está disponible en ese horario! Puedes continuar con tu solicitud."
        : "El espacio no está disponible en ese horario.";
  } catch (error) {
    notify(error.message, true);
  }
});

bindForm("reservation-form", async (event) => {
  const form = event.currentTarget;
  try {
    const interval = readInterval(form);
    const reservation = await request("/reservations", {
      method: "POST",
      body: JSON.stringify({ space_id: Number(form.elements.space_id.value), ...interval }),
    });
    form.reset();
    await refreshApplication();
    notify(`Solicitud #${reservation.id} creada. Estado: ${reservation.status}.`);
  } catch (error) {
    notify(error.message, true);
  }
});

bindForm("space-form", async (event) => {
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  values.capacity = Number(values.capacity);
  try {
    const space = await request("/spaces", { method: "POST", body: JSON.stringify(values) });
    form.reset();
    await refreshApplication();
    notify(`Espacio “${space.name}” creado y asignado a tu ámbito.`);
  } catch (error) {
    notify(error.message, true);
  }
});

bindForm("space-edit-form", async (event) => {
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const spaceId = Number(values.space_id);
  delete values.space_id;
  values.capacity = Number(values.capacity);
  try {
    await request(`/spaces/${spaceId}`, { method: "PUT", body: JSON.stringify(values) });
    byId("space-edit-dialog").close();
    await refreshApplication();
    notify("Cambios del espacio guardados.");
  } catch (error) {
    notify(error.message, true);
  }
});

bindForm("role-form", async (event) => {
  const values = Object.fromEntries(new FormData(event.currentTarget));
  try {
    await request(`/users/${Number(values.user_id)}/roles/${encodeURIComponent(values.role_name)}`, { method: "PUT" });
    await refreshApplication();
    notify("Rol asignado correctamente.");
  } catch (error) {
    notify(error.message, true);
  }
});

bindForm("space-assignment-form", async (event) => {
  const values = Object.fromEntries(new FormData(event.currentTarget));
  try {
    await request(`/users/${Number(values.user_id)}/spaces/${Number(values.space_id)}`, { method: "PUT" });
    notify("Espacio asignado al administrador correctamente.");
  } catch (error) {
    notify(error.message, true);
  }
});

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", () => showPanel(button.dataset.panel));
});

document.addEventListener("click", async (event) => {
  const panelButton = event.target.closest("[data-go-panel]");
  if (panelButton) showPanel(panelButton.dataset.goPanel);

  const closeButton = event.target.closest("[data-close-dialog]");
  if (closeButton) byId("history-dialog").close();

  const action = event.target.closest("[data-action]");
  if (!action) return;
  const id = Number(action.dataset.id);
  try {
    if (action.dataset.action === "history") {
      const events = await request(`/reservations/${id}/history`);
      byId("history-content").innerHTML = events.length
        ? events.map((item) => `<article class="data-card"><h3>${escapeHtml(item.event_type)}</h3><p>${escapeHtml(formatDate(item.occurred_at))}</p><p>${escapeHtml(JSON.stringify(item.details))}</p></article>`).join("")
        : renderEmpty("No hay eventos en el historial.");
      byId("history-dialog").showModal();
    } else if (action.dataset.action === "approve") {
      if (!window.confirm("¿Confirmas la aprobación de esta solicitud?")) return;
      await request(`/reservations/${id}/approve`, { method: "POST" });
      await refreshApplication();
      notify("Solicitud aprobada correctamente.");
    } else if (action.dataset.action === "reject") {
      const reason = window.prompt("Escribe el motivo del rechazo:");
      if (!reason?.trim()) return;
      await request(`/reservations/${id}/reject`, { method: "POST", body: JSON.stringify({ reason: reason.trim() }) });
      await refreshApplication();
      notify("Solicitud rechazada y motivo registrado.");
    } else if (action.dataset.action === "cancel") {
      const ownRequest = action.dataset.own === "true";
      if (!window.confirm("¿Quieres cancelar esta solicitud?")) return;
      const reason = ownRequest ? null : window.prompt("Escribe el motivo de cancelación administrativa:");
      if (!ownRequest && !reason?.trim()) return;
      await request(`/reservations/${id}/cancel`, { method: "POST", body: JSON.stringify(reason ? { reason: reason.trim() } : {}) });
      await refreshApplication();
      notify("Solicitud cancelada.");
    } else if (action.dataset.action === "toggle-space") {
      const isActive = action.dataset.active === "true";
      await request(`/spaces/${id}/status`, { method: "PATCH", body: JSON.stringify({ is_active: !isActive }) });
      await refreshApplication();
      notify(isActive ? "Espacio desactivado." : "Espacio activado.");
    } else if (action.dataset.action === "edit-space") {
      const space = state.spaces.find((item) => item.id === id);
      if (!space) return;
      const form = byId("space-edit-form");
      form.elements.space_id.value = String(space.id);
      form.elements.name.value = space.name;
      if (![...form.elements.space_type.options].some((option) => option.value === space.space_type)) {
        form.elements.space_type.add(new Option(space.space_type, space.space_type));
      }
      form.elements.space_type.value = space.space_type;
      form.elements.capacity.value = String(space.capacity);
      form.elements.location.value = space.location;
      byId("space-edit-dialog").showModal();
    } else if (action.dataset.action === "delete-space") {
      if (!window.confirm("¿Eliminar este espacio? Solo se puede si no tiene solicitudes asociadas.")) return;
      await request(`/spaces/${id}`, { method: "DELETE" });
      await refreshApplication();
      notify("Espacio eliminado.");
    } else if (action.dataset.action === "toggle-account") {
      const isActive = action.dataset.active === "true";
      await request(`/users/${id}/status`, { method: "PATCH", body: JSON.stringify({ is_active: !isActive }) });
      await refreshApplication();
      notify(isActive ? "Cuenta desactivada." : "Cuenta activada.");
    }
  } catch (error) {
    notify(error.message, true);
  }
});

byId("logout-button").addEventListener("click", () => clearSession());

async function restoreSession() {
  if (!state.token) return;
  try {
    state.user = await request("/auth/me");
    await refreshApplication();
    showPanel("overview-panel");
  } catch (error) {
    if (state.token) notify(error.message, true);
  }
}

restoreSession();
