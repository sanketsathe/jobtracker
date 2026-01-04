(function() {
    const drawer = document.getElementById("drawer");
    const backdrop = document.getElementById("drawerBackdrop");
    if (!drawer || !backdrop) {
        return;
    }

    const selectedClass = "is-selected";
    const drawerOpenClass = "open";
    let lastFocusedRow = null;
    let selectedAppId = null;
    let drawerRequestId = 0;
    let saveTimer = null;
    let saveInFlight = false;
    let queuedSave = false;
    let pendingPayload = {};
    let lastSavePayload = null;
    let lastFailedPayload = null;
    let saveStatusTimeout = null;
    let saveFadeTimeout = null;

    function isInteractive(target) {
        if (!target) {
            return false;
        }
        return Boolean(
            target.closest(
                "a, button, input, select, textarea, label, summary, [data-stop-rowclick]"
            )
        );
    }

    function getRowById(appId) {
        return document.querySelector(`.app-row[data-app-id="${appId}"]`);
    }

    function setSelected(pk) {
        const selectedValue = pk ? String(pk) : null;
        selectedAppId = selectedValue;
        document.querySelectorAll(".app-row").forEach((row) => {
            row.classList.toggle(
                selectedClass,
                selectedValue && row.dataset.appId === selectedValue
            );
        });
    }

    function updateSelectedParam(pk) {
        const url = new URL(window.location.href);
        if (pk) {
            url.searchParams.set("selected", pk);
        } else {
            url.searchParams.delete("selected");
        }
        window.history.replaceState({}, "", url.toString());
    }

    function getQueryWithoutSelected() {
        const params = new URLSearchParams(window.location.search);
        params.delete("selected");
        const query = params.toString();
        return query ? `?${query}` : "";
    }

    function isDebugDrawer() {
        return window.DEBUG_DRAWER === true;
    }

    function updateTopbarHeight() {
        const topbar = document.querySelector(".topbar");
        const root = document.documentElement;
        if (!topbar || !root) {
            if (root) {
                root.style.setProperty("--topbar-h", "0px");
            }
            return;
        }
        const rect = topbar.getBoundingClientRect();
        root.style.setProperty("--topbar-h", `${rect.height}px`);
    }

    function ensureDrawerActionIcons(scopeEl) {
        if (!scopeEl) {
            return;
        }
        const maximize = scopeEl.querySelector(".drawer-maximize");
        if (maximize && !maximize.querySelector("svg")) {
            const trimmed = maximize.innerHTML.trim();
            if (!trimmed) {
                maximize.innerHTML = `
                    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                        <path d="M3 9V3h6" />
                        <path d="M21 9V3h-6" />
                        <path d="M3 15v6h6" />
                        <path d="M21 15v6h-6" />
                    </svg>
                `.trim();
            }
        }
        const close = scopeEl.querySelector(".drawer-close");
        if (close && !close.querySelector("svg")) {
            const trimmed = close.innerHTML.trim();
            if (!trimmed) {
                close.innerHTML = `
                    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                        <path d="M6 6l12 12" />
                        <path d="M18 6l-12 12" />
                    </svg>
                `.trim();
            }
        }
    }

    function getSaveIconMarkup(state) {
        if (state === "saving") {
            return `
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 3v4" />
                </svg>
            `.trim();
        }
        if (state === "saved") {
            return `
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M5 12l4 4 10-10" />
                </svg>
            `.trim();
        }
        if (state === "error") {
            return `
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M12 8v5" />
                    <path d="M12 17h.01" />
                    <path d="M4 20h16L12 4 4 20z" />
                </svg>
            `.trim();
        }
        return "";
    }

    function showDrawer(html) {
        drawer.innerHTML = html;
        drawer.setAttribute("aria-hidden", "false");
        drawer.removeAttribute("aria-busy");
        drawer.classList.add(drawerOpenClass);
        backdrop.hidden = false;
        resetSaveState();
        ensureDrawerActionIcons(drawer);
        updateTopbarHeight();
        if (isDebugDrawer()) {
            document.documentElement.classList.add("debug-drawer");
            console.log("drawer html:", drawer.innerHTML.slice(0, 500));
            const maximize = drawer.querySelector(".drawer-maximize");
            console.log("maximize el:", maximize);
            console.log(
                "maximize svg:",
                maximize ? Boolean(maximize.querySelector("svg")) : false
            );
            console.log(
                "maximize html length:",
                maximize ? maximize.innerHTML.trim().length : 0
            );
            console.log("header el:", drawer.querySelector(".drawer-header"));
            if (maximize) {
                const rect = maximize.getBoundingClientRect();
                const drawerRect = drawer.getBoundingClientRect();
                console.log("drawer rect:", drawerRect);
                console.log("maximize rect:", rect);
                const computed = window.getComputedStyle(maximize);
                console.log("maximize styles:", {
                    position: computed.position,
                    top: computed.top,
                    right: computed.right,
                    zIndex: computed.zIndex,
                    opacity: computed.opacity,
                    visibility: computed.visibility,
                    color: computed.color,
                });
                const svg = maximize.querySelector("svg");
                if (svg) {
                    const svgStyle = window.getComputedStyle(svg);
                    console.log("maximize svg styles:", {
                        display: svgStyle.display,
                        opacity: svgStyle.opacity,
                        visibility: svgStyle.visibility,
                        stroke: svgStyle.stroke,
                        fill: svgStyle.fill,
                    });
                }
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const atPoint = document.elementFromPoint(centerX, centerY);
                console.log("elementFromPoint:", atPoint);
            }
        }
    }

    function showDrawerError(message) {
        drawer.innerHTML = `
            <div class="drawer-panel">
                <div class="drawer-header">
                    <div>
                        <h2 class="drawer-title">Unable to load details</h2>
                        <div class="drawer-subtitle text-subtle">${message}</div>
                    </div>
                    <div class="drawer-header-actions">
                        <button type="button" class="icon-btn icon-btn--ghost drawer-close" data-drawer-close aria-label="Close">
                            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                                <path d="M6 6l12 12" />
                                <path d="M18 6l-12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
        drawer.setAttribute("aria-hidden", "false");
        drawer.removeAttribute("aria-busy");
        drawer.classList.add(drawerOpenClass);
        backdrop.hidden = false;
        ensureDrawerActionIcons(drawer);
        updateTopbarHeight();
    }

    function openDrawerForRow(row) {
        if (!row) {
            return;
        }
        const pk = row.dataset.appId;
        const drawerUrl = row.dataset.drawerUrl;
        if (!pk || !drawerUrl) {
            return;
        }

        lastFocusedRow = row;
        setSelected(pk);
        updateSelectedParam(pk);
        const requestId = ++drawerRequestId;
        drawer.setAttribute("aria-busy", "true");

        const query = getQueryWithoutSelected();
        const cacheBuster = `cb=${Date.now()}`;
        const requestUrl = `${drawerUrl}${query}${query ? "&" : "?"}${cacheBuster}`;
        if (isDebugDrawer()) {
            console.log("drawer fetch url:", requestUrl);
        }
        fetch(requestUrl, { credentials: "same-origin", cache: "no-store" })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Drawer load failed: ${response.status}`);
                }
                return response.text();
            })
            .then((html) => {
                if (requestId !== drawerRequestId || selectedAppId !== String(pk)) {
                    return;
                }
                showDrawer(html);
            })
            .catch((error) => {
                if (requestId !== drawerRequestId || selectedAppId !== String(pk)) {
                    return;
                }
                console.error(error);
                showDrawerError("Please try again.");
            });
    }

    function closeDrawer() {
        drawer.innerHTML = "";
        drawer.setAttribute("aria-hidden", "true");
        drawer.removeAttribute("aria-busy");
        drawer.classList.remove(drawerOpenClass);
        backdrop.hidden = true;
        setSelected(null);
        updateSelectedParam(null);
        drawerRequestId += 1;
        resetSaveState();
        if (lastFocusedRow) {
            lastFocusedRow.focus();
        }
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    }

    function updateFollowupElement(el, value) {
        if (!el) {
            return;
        }
        const display = value || "—";
        el.textContent = display;
        if (display === "—") {
            el.classList.add("followup--none");
        } else {
            el.classList.remove("followup--none");
        }
    }

    function updateRow(row, payload) {
        if (!row || !payload) {
            return;
        }
        const statusEl = row.querySelector("[data-status-display]");
        if (statusEl && payload.status_label) {
            statusEl.textContent = payload.status_label;
        }
        updateFollowupElement(
            row.querySelector("[data-followup-display]"),
            payload.follow_up_display
        );
        const appliedEl = row.querySelector("[data-applied-display]");
        if (appliedEl && payload.applied_display) {
            appliedEl.textContent = payload.applied_display;
        }
        const notesEl = row.querySelector("[data-notes-display]");
        if (notesEl && Object.prototype.hasOwnProperty.call(payload, "notes")) {
            notesEl.textContent = payload.notes ? payload.notes : "—";
        }
    }

    function updateDrawer(payload) {
        updateFollowupElement(
            drawer.querySelector("[data-drawer-followup]"),
            payload.follow_up_display
        );
        const appliedEl = drawer.querySelector("[data-drawer-applied]");
        if (appliedEl && payload.applied_display) {
            appliedEl.textContent = payload.applied_display;
        }
        const statusSelect = drawer.querySelector("[data-quick-status]");
        if (statusSelect && payload.status) {
            statusSelect.value = payload.status;
        }
        const notesInput = drawer.querySelector("[data-quick-notes]");
        if (
            notesInput &&
            Object.prototype.hasOwnProperty.call(payload, "notes") &&
            document.activeElement !== notesInput
        ) {
            notesInput.value = payload.notes || "";
        }
        const followUpInput = drawer.querySelector("[data-followup-date]");
        if (followUpInput && Object.prototype.hasOwnProperty.call(payload, "follow_up_value")) {
            const value = payload.follow_up_value || "";
            followUpInput.value = value ? value.split("T")[0] : "";
        }
    }

    function applyQuickUpdate(payload, sourceRow) {
        const targetRow = sourceRow || getRowById(payload.id);
        if (targetRow) {
            updateRow(targetRow, payload);
        }
        const drawerBody = drawer.querySelector("[data-app-id]");
        if (
            drawerBody &&
            payload.id &&
            drawerBody.dataset.appId === String(payload.id)
        ) {
            updateDrawer(payload);
        }
    }

    function setSaveStatus(state) {
        const statusEl = drawer.querySelector("[data-save-status]");
        if (!statusEl) {
            return;
        }
        statusEl.classList.remove("is-saving", "is-error", "is-saved", "is-fading");
        if (saveStatusTimeout) {
            window.clearTimeout(saveStatusTimeout);
            saveStatusTimeout = null;
        }
        if (saveFadeTimeout) {
            window.clearTimeout(saveFadeTimeout);
            saveFadeTimeout = null;
        }
        if (state === "saving") {
            statusEl.innerHTML = getSaveIconMarkup("saving");
            statusEl.setAttribute("aria-label", "Saving…");
            statusEl.setAttribute("title", "Saving…");
            statusEl.classList.add("is-saving");
            return;
        }
        if (state === "error") {
            statusEl.innerHTML = getSaveIconMarkup("error");
            statusEl.setAttribute("aria-label", "Error — click to retry");
            statusEl.setAttribute("title", "Error — click to retry");
            statusEl.classList.add("is-error");
            return;
        }
        if (state === "saved") {
            statusEl.innerHTML = getSaveIconMarkup("saved");
            statusEl.setAttribute("aria-label", "Saved");
            statusEl.setAttribute("title", "Saved");
            statusEl.classList.add("is-saved");
            saveStatusTimeout = window.setTimeout(() => {
                statusEl.classList.add("is-fading");
                saveFadeTimeout = window.setTimeout(() => {
                    statusEl.classList.remove("is-saved", "is-fading");
                    statusEl.innerHTML = "";
                }, 250);
            }, 1000);
            return;
        }
        statusEl.innerHTML = "";
    }

    function resetSaveState() {
        if (saveTimer) {
            window.clearTimeout(saveTimer);
            saveTimer = null;
        }
        if (saveStatusTimeout) {
            window.clearTimeout(saveStatusTimeout);
            saveStatusTimeout = null;
        }
        if (saveFadeTimeout) {
            window.clearTimeout(saveFadeTimeout);
            saveFadeTimeout = null;
        }
        saveInFlight = false;
        queuedSave = false;
        pendingPayload = {};
        lastSavePayload = null;
        lastFailedPayload = null;
        setSaveStatus("idle");
    }

    function postQuickAction(url, payload, sourceRow, menu, options = {}) {
        const csrfToken = getCookie("csrftoken");
        const isJson = options.json !== false;
        return fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": isJson
                    ? "application/json;charset=UTF-8"
                    : "application/x-www-form-urlencoded;charset=UTF-8",
            },
            body: isJson ? JSON.stringify(payload) : new URLSearchParams(payload),
        })
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((data) => {
                        throw new Error(data.error || "Quick update failed.");
                    });
                }
                return response.json();
            })
            .then((data) => {
                applyQuickUpdate(data, sourceRow);
                if (menu) {
                    menu.open = false;
                }
                return data;
            })
            .catch((error) => {
                console.error(error);
                throw error;
            });
    }

    function scheduleSave() {
        if (saveTimer) {
            window.clearTimeout(saveTimer);
        }
        saveTimer = window.setTimeout(() => {
            saveTimer = null;
            flushSave();
        }, 600);
    }

    function queueImmediateSave(payload, menu) {
        pendingPayload = { ...pendingPayload, ...payload };
        if (menu) {
            menu.open = false;
        }
        if (saveTimer) {
            window.clearTimeout(saveTimer);
            saveTimer = null;
        }
        flushSave();
    }

    function flushSave() {
        if (saveInFlight) {
            queuedSave = true;
            return;
        }
        if (!Object.keys(pendingPayload).length) {
            return;
        }
        const drawerBody = drawer.querySelector("[data-app-id]");
        const activeDrawerId = drawerBody ? drawerBody.dataset.appId : null;
        const url = drawerBody ? drawerBody.dataset.quickUrl : "";
        if (!url) {
            return;
        }
        const payload = pendingPayload;
        pendingPayload = {};
        saveInFlight = true;
        setSaveStatus("saving");
        lastSavePayload = payload;
        postQuickAction(url, payload, getRowById(selectedAppId))
            .then((data) => {
                if (
                    !drawerBody ||
                    !data ||
                    String(data.id) !== activeDrawerId
                ) {
                    return;
                }
                lastFailedPayload = null;
                setSaveStatus("saved");
            })
            .catch(() => {
                pendingPayload = { ...payload, ...pendingPayload };
                lastFailedPayload = payload;
                const currentDrawer = drawer.querySelector("[data-app-id]");
                if (currentDrawer && currentDrawer.dataset.appId === activeDrawerId) {
                    setSaveStatus("error");
                }
            })
            .finally(() => {
                saveInFlight = false;
                if (queuedSave) {
                    queuedSave = false;
                    flushSave();
                }
            });
    }

    document.addEventListener("click", (event) => {
        const closeTarget = event.target.closest("[data-drawer-close]");
        if (closeTarget) {
            closeDrawer();
            return;
        }

        const presetButton = event.target.closest("[data-followup-preset]");
        if (presetButton) {
            setSaveStatus("saving");
            queueImmediateSave(
                { followup: { preset: presetButton.dataset.followupPreset } },
                presetButton.closest("details")
            );
            return;
        }

        const clearButton = event.target.closest("[data-followup-clear]");
        if (clearButton) {
            setSaveStatus("saving");
            queueImmediateSave(
                { followup: { preset: "clear" } },
                clearButton.closest("details")
            );
            return;
        }

        const dateButton = event.target.closest("[data-followup-date-submit]");
        if (dateButton) {
            const panel = dateButton.closest(".snooze-panel");
            const input = panel ? panel.querySelector("[data-followup-date]") : null;
            const value = input ? input.value : "";
            if (!value) {
                return;
            }
            setSaveStatus("saving");
            queueImmediateSave(
                { followup: { preset: "date", date: value } },
                dateButton.closest("details")
            );
        }
    });

    document.addEventListener("click", (event) => {
        const saveButton = event.target.closest("[data-save-status]");
        if (!saveButton) {
            return;
        }
        if (!saveButton.classList.contains("is-error")) {
            return;
        }
        if (lastFailedPayload) {
            pendingPayload = { ...lastFailedPayload, ...pendingPayload };
            lastFailedPayload = null;
            setSaveStatus("saving");
            flushSave();
        }
    });

    drawer.addEventListener("change", (event) => {
        const statusSelect = event.target.closest("[data-quick-status]");
        if (statusSelect) {
            setSaveStatus("saving");
            queueImmediateSave({ status: statusSelect.value });
            return;
        }
    });

    drawer.addEventListener("input", (event) => {
        const notesInput = event.target.closest("[data-quick-notes]");
        if (notesInput) {
            pendingPayload.notes = notesInput.value;
            scheduleSave();
        }
    });

    backdrop.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeDrawer();
        }
        if (event.key === "Enter" || event.key === " ") {
            if (isInteractive(event.target)) {
                return;
            }
            const row = event.target.closest(".app-row");
            if (row) {
                event.preventDefault();
                openDrawerForRow(row);
            }
        }
    });

    document.addEventListener("click", (event) => {
        if (isInteractive(event.target)) {
            return;
        }
        const row = event.target.closest(".app-row");
        if (!row) {
            return;
        }
        openDrawerForRow(row);
    });

    const selected = new URLSearchParams(window.location.search).get("selected");
    if (selected) {
        const row = getRowById(selected);
        if (row) {
            openDrawerForRow(row);
        } else {
            updateSelectedParam(null);
        }
    }

    updateTopbarHeight();
    window.addEventListener("resize", updateTopbarHeight);

    function warnOnDuplicateIds() {
        const seen = new Map();
        const duplicates = new Map();
        document.querySelectorAll("[id]").forEach((el) => {
            const id = el.id;
            if (!id) {
                return;
            }
            if (seen.has(id)) {
                duplicates.set(id, true);
            } else {
                seen.set(id, true);
            }
        });
        if (duplicates.size) {
            console.warn(
                "Duplicate element ids detected:",
                Array.from(duplicates.keys())
            );
        }
    }

    warnOnDuplicateIds();
})();
