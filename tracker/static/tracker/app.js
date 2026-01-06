(function() {
    const overlayRoot = document.getElementById("overlay-root");
    const toastContainer = document.getElementById("toastContainer");
    const body = document.body;
    const root = document.documentElement;
    const mobileQuery = window.matchMedia("(max-width: 900px)");

    const SAVE_DEBOUNCE_MS = 700;
    const savedDisplayMs = 1200;
    const savedFadeMs = 250;

    const state = {
        selectedId: null,
        anchorEl: null,
        lastFocused: null,
        popover: null,
        modal: null,
        modalBackdrop: null,
        modalRoot: null,
        popoverRoot: null,
        activeEditor: null,
        activeMode: null,
        pendingPayload: {},
        lastFieldSnapshot: {},
        saveTimer: null,
        saveInFlight: false,
        queuedSave: false,
        lastFailedPayload: null,
        lastUndoCandidate: null,
        saveStatusTimeout: null,
        saveFadeTimeout: null,
        lastSavedAt: null,
        saveTextTimer: null,
        popoverRequestId: 0,
        modalRequestId: 0,
        focusTrapHandler: null,
    };

    function isMobile() {
        return mobileQuery.matches;
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    }

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

    function setSelectedRow(appId) {
        state.selectedId = appId ? String(appId) : null;
        document.querySelectorAll(".app-row").forEach((row) => {
            row.classList.toggle(
                "is-selected",
                state.selectedId && row.dataset.appId === state.selectedId
            );
        });
    }

    function updateSelectedParam(appId) {
        const url = new URL(window.location.href);
        if (appId) {
            url.searchParams.set("selected", appId);
        } else {
            url.searchParams.delete("selected");
        }
        window.history.replaceState({}, "", url.toString());
    }

    function ensureOverlayContainers() {
        if (!overlayRoot) {
            return null;
        }
        if (!state.popoverRoot) {
            const popoverRoot = document.createElement("div");
            popoverRoot.className = "popover-root";
            const modalBackdrop = document.createElement("div");
            modalBackdrop.className = "modal-backdrop";
            modalBackdrop.hidden = true;
            const modalRoot = document.createElement("div");
            modalRoot.className = "modal-root";
            overlayRoot.appendChild(popoverRoot);
            overlayRoot.appendChild(modalBackdrop);
            overlayRoot.appendChild(modalRoot);
            state.popoverRoot = popoverRoot;
            state.modalBackdrop = modalBackdrop;
            state.modalRoot = modalRoot;
            modalBackdrop.addEventListener("click", () => {
                closeModal();
            });
        }
        return {
            popoverRoot: state.popoverRoot,
            modalBackdrop: state.modalBackdrop,
            modalRoot: state.modalRoot,
        };
    }

    function showToast(message, actionLabel, onAction) {
        if (!toastContainer) {
            return;
        }
        toastContainer.innerHTML = "";
        const toast = document.createElement("div");
        toast.className = "toast";
        const text = document.createElement("div");
        text.className = "toast-message";
        text.textContent = message;
        toast.appendChild(text);

        if (actionLabel && onAction) {
            const actionBtn = document.createElement("button");
            actionBtn.type = "button";
            actionBtn.className = "btn btn-quiet btn-compact";
            actionBtn.textContent = actionLabel;
            actionBtn.addEventListener("click", () => {
                onAction();
                toast.remove();
            });
            toast.appendChild(actionBtn);
        }

        toastContainer.appendChild(toast);
        window.setTimeout(() => {
            toast.remove();
        }, 8000);
    }

    function showUndoToast(message, undoPayload) {
        const editor = state.activeEditor;
        const url = editor ? editor.dataset.patchUrl : "";
        if (!url) {
            return;
        }
        showToast(message, "Undo", () => {
            setSaveStatus("saving");
            sendPatch(url, undoPayload)
                .then((data) => {
                    applyPatchUpdate(data.application, getRowById(data.application.id));
                    setLastSavedAt(data.saved_at);
                    setSaveStatus("saved");
                })
                .catch(() => {
                    setSaveStatus("error");
                });
        });
    }

    function clearSaveStatusTimers() {
        if (state.saveStatusTimeout) {
            window.clearTimeout(state.saveStatusTimeout);
            state.saveStatusTimeout = null;
        }
        if (state.saveFadeTimeout) {
            window.clearTimeout(state.saveFadeTimeout);
            state.saveFadeTimeout = null;
        }
    }

    function formatRelativeTime(timestamp) {
        const seconds = Math.floor((Date.now() - timestamp.getTime()) / 1000);
        if (seconds < 10) {
            return "Saved just now";
        }
        if (seconds < 60) {
            return `Saved ${seconds}s ago`;
        }
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) {
            return `Saved ${minutes}m ago`;
        }
        const hours = Math.floor(minutes / 60);
        return `Saved ${hours}h ago`;
    }

    function updateSaveText() {
        const editor = state.activeEditor;
        if (!editor) {
            return;
        }
        const textEl = editor.querySelector("[data-save-text]");
        if (!textEl) {
            return;
        }
        if (!state.lastSavedAt) {
            textEl.textContent = "Not saved yet";
            return;
        }
        textEl.textContent = formatRelativeTime(state.lastSavedAt);
    }

    function startSaveTextTimer() {
        if (state.saveTextTimer) {
            window.clearInterval(state.saveTextTimer);
        }
        state.saveTextTimer = window.setInterval(updateSaveText, 30000);
    }

    function setLastSavedAt(isoString) {
        if (!isoString) {
            return;
        }
        const parsed = new Date(isoString);
        if (Number.isNaN(parsed.getTime())) {
            return;
        }
        state.lastSavedAt = parsed;
        updateSaveText();
        startSaveTextTimer();
    }

    function setSaveStatus(stateName) {
        const editor = state.activeEditor;
        if (!editor) {
            return;
        }
        const statusEl = editor.querySelector("[data-save-status]");
        const textEl = editor.querySelector("[data-save-text]");
        if (!statusEl) {
            return;
        }
        clearSaveStatusTimers();
        statusEl.classList.remove("is-idle", "is-saving", "is-saved", "is-error", "is-fading");

        if (stateName === "saving") {
            statusEl.classList.add("is-saving");
            statusEl.setAttribute("title", "Saving");
            if (textEl) {
                textEl.textContent = "Saving...";
            }
            return;
        }
        if (stateName === "error") {
            statusEl.classList.add("is-error");
            statusEl.setAttribute("title", "Save failed. Click to retry");
            if (textEl) {
                textEl.textContent = "Save failed. Retry.";
            }
            return;
        }
        if (stateName === "saved") {
            statusEl.classList.add("is-saved");
            statusEl.setAttribute("title", "Saved");
            state.saveStatusTimeout = window.setTimeout(() => {
                statusEl.classList.add("is-fading");
                state.saveFadeTimeout = window.setTimeout(() => {
                    setSaveStatus("idle");
                }, savedFadeMs);
            }, savedDisplayMs);
            updateSaveText();
            return;
        }
        statusEl.classList.add("is-idle");
        statusEl.setAttribute("title", "");
        if (textEl) {
            updateSaveText();
        }
    }

    function resetSaveState() {
        if (state.saveTimer) {
            window.clearTimeout(state.saveTimer);
            state.saveTimer = null;
        }
        clearSaveStatusTimers();
        state.saveInFlight = false;
        state.queuedSave = false;
        state.pendingPayload = {};
        state.lastFailedPayload = null;
        state.lastUndoCandidate = null;
        state.lastSavedAt = null;
        if (state.saveTextTimer) {
            window.clearInterval(state.saveTextTimer);
            state.saveTextTimer = null;
        }
        setSaveStatus("idle");
        updateSaveText();
    }

    function refreshFieldSnapshot(container) {
        state.lastFieldSnapshot = {};
        if (!container) {
            return;
        }
        container.querySelectorAll("[data-autosave]").forEach((input) => {
            const field = input.dataset.autosave;
            if (!field) {
                return;
            }
            state.lastFieldSnapshot[field] = input.value;
        });
    }

    function clearFieldErrors(container, fieldName) {
        if (!container) {
            return;
        }
        const selector = fieldName ? `[data-field-error="${fieldName}"]` : "[data-field-error]";
        container.querySelectorAll(selector).forEach((el) => {
            el.textContent = "";
        });
    }

    function applyFieldErrors(container, fieldErrors) {
        if (!container) {
            return;
        }
        clearFieldErrors(container);
        if (!fieldErrors) {
            return;
        }
        Object.entries(fieldErrors).forEach(([field, message]) => {
            const target = container.querySelector(`[data-field-error="${field}"]`);
            if (target) {
                target.textContent = message;
            }
        });
    }

    function sendPatch(url, payload) {
        const csrfToken = getCookie("csrftoken");
        const requestInit = {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json;charset=UTF-8",
            },
            body: JSON.stringify(payload),
        };
        return fetch(url, requestInit)
            .then((response) => {
                if (response.status === 405) {
                    return fetch(url, { ...requestInit, method: "POST" });
                }
                return response;
            })
            .then((response) => {
                return response.json().then((data) => {
                    if (!response.ok || !data.ok) {
                        const error = new Error(data.error || "Save failed.");
                        error.fieldErrors = data.field_errors || {};
                        throw error;
                    }
                    return data;
                });
            });
    }

    function scheduleSave() {
        if (state.saveTimer) {
            window.clearTimeout(state.saveTimer);
        }
        state.saveTimer = window.setTimeout(() => {
            state.saveTimer = null;
            flushSave();
        }, SAVE_DEBOUNCE_MS);
    }

    function queueImmediateSave(payload) {
        state.pendingPayload = { ...state.pendingPayload, ...payload };
        if (state.saveTimer) {
            window.clearTimeout(state.saveTimer);
            state.saveTimer = null;
        }
        flushSave();
    }

    function flushSave() {
        if (state.saveInFlight) {
            state.queuedSave = true;
            return;
        }
        if (!Object.keys(state.pendingPayload).length) {
            return;
        }
        const editor = state.activeEditor;
        if (!editor) {
            return;
        }
        const url = editor.dataset.patchUrl;
        if (!url) {
            return;
        }
        const payload = state.pendingPayload;
        state.pendingPayload = {};
        state.saveInFlight = true;
        setSaveStatus("saving");
        const activeId = editor.dataset.appId;
        sendPatch(url, payload)
            .then((data) => {
                if (!editor || String(data.application.id) !== String(activeId)) {
                    return;
                }
                state.lastFailedPayload = null;
                applyPatchUpdate(data.application, getRowById(data.application.id));
                setLastSavedAt(data.saved_at);
                setSaveStatus("saved");
                if (state.lastUndoCandidate) {
                    const candidate = state.lastUndoCandidate;
                    state.lastUndoCandidate = null;
                    if (candidate.field === "status") {
                        showUndoToast(
                            `Status changed to ${data.application.status_label}.`,
                            { status: candidate.fromValue }
                        );
                    }
                    if (candidate.field === "follow_up_on" && !candidate.toValue) {
                        showUndoToast(
                            "Follow-up date cleared.",
                            { follow_up_on: candidate.fromValue }
                        );
                    }
                }
            })
            .catch((error) => {
                state.pendingPayload = { ...payload, ...state.pendingPayload };
                state.lastFailedPayload = payload;
                if (editor && editor.dataset.appId === activeId) {
                    setSaveStatus("error");
                    applyFieldErrors(editor, error.fieldErrors);
                    showToast("Could not save. Retry.");
                }
            })
            .finally(() => {
                state.saveInFlight = false;
                if (state.queuedSave) {
                    state.queuedSave = false;
                    flushSave();
                }
            });
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

    function updateFollowupBadge(row, followUpOn) {
        if (!row) {
            return;
        }
        const badge = row.querySelector("[data-followup-badge]");
        if (badge) {
            badge.remove();
        }

        const followupDate = followUpOn ? new Date(`${followUpOn}T00:00:00`) : null;
        if (!followupDate || Number.isNaN(followupDate.getTime())) {
            return;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const weekEnd = new Date(today);
        weekEnd.setDate(weekEnd.getDate() + 7);

        let text = "";
        let className = "";
        if (followupDate < today) {
            text = "Overdue";
            className = "badge badge--danger";
        } else if (followupDate.getTime() === today.getTime()) {
            text = "Today";
            className = "badge badge--warning";
        } else if (followupDate <= weekEnd) {
            text = "This week";
            className = "badge badge--info";
        }

        if (!text) {
            return;
        }

        const badgeEl = document.createElement("span");
        badgeEl.className = className;
        badgeEl.textContent = text;
        badgeEl.setAttribute("data-followup-badge", "");
        const followupCell = row.querySelector("[data-col='followup']");
        if (followupCell) {
            followupCell.appendChild(badgeEl);
        }
    }

    function updateRow(row, payload) {
        if (!row || !payload) {
            return;
        }
        const statusEl = row.querySelector("[data-status-display]");
        if (statusEl && payload.status_label) {
            statusEl.textContent = payload.status_label;
            const nextClass = `badge-status--${payload.status.toLowerCase()}`;
            statusEl.className = `badge-status ${nextClass}`;
        }
        updateFollowupElement(row.querySelector("[data-followup-display]"), payload.follow_up_display);
        updateFollowupBadge(row, payload.follow_up_on);
        const nextActionEl = row.querySelector("[data-next-action-display]");
        if (nextActionEl && Object.prototype.hasOwnProperty.call(payload, "next_action")) {
            nextActionEl.textContent = payload.next_action ? payload.next_action : "—";
        }
        const notesEl = row.querySelector("[data-notes-display]");
        if (notesEl && Object.prototype.hasOwnProperty.call(payload, "notes")) {
            notesEl.textContent = payload.notes ? payload.notes : "—";
        }
        const titleEl = row.querySelector("[data-title-display]");
        if (titleEl && payload.title) {
            titleEl.textContent = payload.title;
        }
        const companyEl = row.querySelector("[data-company-display]");
        if (companyEl && payload.company) {
            companyEl.textContent = payload.company;
        }
        const locationEl = row.querySelector("[data-location-display]");
        if (locationEl && Object.prototype.hasOwnProperty.call(payload, "location_text")) {
            locationEl.textContent = payload.location_text || "";
            const wrap = row.querySelector("[data-location-wrap]");
            if (wrap) {
                wrap.hidden = !payload.location_text;
            }
        }
        const linkEl = row.querySelector("[data-job-url-display]");
        if (linkEl && Object.prototype.hasOwnProperty.call(payload, "job_url")) {
            if (payload.job_url) {
                linkEl.href = payload.job_url;
                const wrap = row.querySelector("[data-job-url-wrap]");
                if (wrap) {
                    wrap.hidden = false;
                }
            } else {
                const wrap = row.querySelector("[data-job-url-wrap]");
                if (wrap) {
                    wrap.hidden = true;
                }
            }
        }
    }

    function updateBoardCard(payload) {
        if (!payload || !payload.id) {
            return;
        }
        const card = document.querySelector(`.kanban-card[data-app-id="${payload.id}"]`);
        if (!card) {
            return;
        }
        const targetColumn = document.querySelector(`.kanban-column[data-status="${payload.status}"]`);
        if (!targetColumn) {
            return;
        }
        const targetList = targetColumn.querySelector(".kanban-cards");
        const currentColumn = card.closest(".kanban-column");
        if (targetList && currentColumn && currentColumn !== targetColumn) {
            const currentCount = currentColumn.querySelector("[data-column-count]");
            const targetCount = targetColumn.querySelector("[data-column-count]");
            if (currentCount) {
                currentCount.textContent = `${Math.max(parseInt(currentCount.textContent || "0", 10) - 1, 0)}`;
            }
            if (targetCount) {
                targetCount.textContent = `${parseInt(targetCount.textContent || "0", 10) + 1}`;
            }
            targetList.prepend(card);
        }
        const moveSelect = card.querySelector("[data-move-select]");
        if (moveSelect) {
            moveSelect.value = payload.status;
            moveSelect.dataset.prevValue = payload.status;
        }
    }

    function updateEditor(payload) {
        const editor = state.activeEditor;
        if (!editor || !payload) {
            return;
        }
        if (payload.id && editor.dataset.appId !== String(payload.id)) {
            return;
        }
        const titleEl = editor.querySelector("[data-app-title]");
        const companyEl = editor.querySelector("[data-app-company]");
        const locationEl = editor.querySelector("[data-app-location]");
        const linkEl = editor.querySelector("[data-app-link]");
        const linkWrap = editor.querySelector("[data-app-link-wrap]");
        if (titleEl && payload.title) {
            titleEl.textContent = payload.title;
        }
        if (companyEl && payload.company) {
            companyEl.textContent = payload.company;
        }
        if (locationEl && Object.prototype.hasOwnProperty.call(payload, "location_text")) {
            locationEl.textContent = payload.location_text || "";
        }
        if (linkEl && Object.prototype.hasOwnProperty.call(payload, "job_url")) {
            if (payload.job_url) {
                linkEl.href = payload.job_url;
                if (linkWrap) {
                    linkWrap.hidden = false;
                }
            } else if (linkWrap) {
                linkWrap.hidden = true;
            }
        }

        editor.querySelectorAll("[data-autosave]").forEach((input) => {
            const field = input.dataset.autosave;
            if (!field || !Object.prototype.hasOwnProperty.call(payload, field)) {
                return;
            }
            if (document.activeElement === input) {
                return;
            }
            input.value = payload[field] || "";
        });
        refreshFieldSnapshot(editor);
    }

    function applyPatchUpdate(payload, sourceRow) {
        const targetRow = sourceRow || getRowById(payload.id);
        if (targetRow) {
            updateRow(targetRow, payload);
        }
        updateEditor(payload);
        updateBoardCard(payload);
    }

    function sendFollowupUpdate(followupId, payload) {
        const csrfToken = getCookie("csrftoken");
        const requestInit = {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/json;charset=UTF-8",
            },
            body: JSON.stringify(payload),
        };
        return fetch(`/followups/${followupId}/`, requestInit)
            .then((response) => {
                if (response.status === 405) {
                    return fetch(`/followups/${followupId}/`, { ...requestInit, method: "POST" });
                }
                return response;
            })
            .then((response) => {
                return response.json().then((data) => {
                    if (!response.ok || !data.ok) {
                        throw new Error(data.error || "Follow-up update failed.");
                    }
                    return data;
                });
            });
    }

    function renderFollowupItem(followup) {
        const item = document.createElement("div");
        item.className = "followup-item";
        item.dataset.followupId = followup.id;
        item.innerHTML = `
            <label class="followup-check">
                <input type="checkbox" data-followup-complete ${followup.is_completed ? "checked" : ""}>
                <span class="sr-only">Mark complete</span>
            </label>
            <input type="date" value="${followup.due_on}" data-followup-due>
            <input type="text" value="${followup.note || ""}" placeholder="Note" data-followup-note>
        `.trim();
        return item;
    }

    function setActiveEditor(container, mode) {
        state.activeEditor = container;
        state.activeMode = mode;
        resetSaveState();
        refreshFieldSnapshot(container);
    }

    function closePopover(clearSelection) {
        if (!state.popoverRoot) {
            return;
        }
        state.popoverRoot.innerHTML = "";
        state.popover = null;
        state.anchorEl = null;
        if (state.activeMode === "popover") {
            state.activeEditor = null;
            state.activeMode = null;
        }
        if (clearSelection) {
            setSelectedRow(null);
            updateSelectedParam(null);
        }
        if (state.lastFocused) {
            state.lastFocused.focus();
        }
    }

    function releaseFocusTrap() {
        if (state.modal && state.focusTrapHandler) {
            state.modal.removeEventListener("keydown", state.focusTrapHandler);
            state.focusTrapHandler = null;
        }
    }

    function closeModal() {
        if (!state.modalRoot || !state.modalBackdrop) {
            return;
        }
        body.classList.remove("modal-open");
        state.modalRoot.innerHTML = "";
        state.modalRoot.classList.remove("is-open");
        state.modalBackdrop.hidden = true;
        state.modal = null;
        releaseFocusTrap();
        if (state.activeMode === "modal") {
            state.activeEditor = null;
            state.activeMode = null;
            setSelectedRow(null);
            updateSelectedParam(null);
        }
        if (state.lastFocused) {
            state.lastFocused.focus();
        }
    }

    function showPopoverSkeleton(container) {
        container.innerHTML = `
            <div class="popover-card popover-skeleton">
                <div class="skeleton skeleton-title"></div>
                <div class="skeleton skeleton-subtitle"></div>
                <div class="skeleton skeleton-block"></div>
                <div class="skeleton skeleton-block"></div>
            </div>
        `.trim();
    }

    function showModalSkeleton(container) {
        container.innerHTML = `
            <div class="modal-panel modal-skeleton">
                <div class="modal-header">
                    <div class="modal-headings">
                        <div class="skeleton skeleton-title"></div>
                        <div class="skeleton skeleton-subtitle"></div>
                    </div>
                    <div class="modal-actions">
                        <div class="skeleton skeleton-icon"></div>
                        <div class="skeleton skeleton-icon"></div>
                    </div>
                </div>
                <div class="modal-body">
                    <div class="skeleton skeleton-block"></div>
                    <div class="skeleton skeleton-block"></div>
                </div>
            </div>
        `.trim();
    }

    function positionPopover(anchorEl, popoverEl) {
        if (!anchorEl || !popoverEl) {
            return;
        }
        const padding = 12;
        const rect = anchorEl.getBoundingClientRect();
        const popRect = popoverEl.getBoundingClientRect();
        let top = rect.bottom + 8;
        if (top + popRect.height > window.innerHeight - padding) {
            top = rect.top - popRect.height - 8;
        }
        top = Math.max(padding, Math.min(top, window.innerHeight - popRect.height - padding));

        let left = rect.left;
        if (left + popRect.width > window.innerWidth - padding) {
            left = window.innerWidth - popRect.width - padding;
        }
        left = Math.max(padding, left);
        popoverEl.style.top = `${top}px`;
        popoverEl.style.left = `${left}px`;
    }

    function openPopover(row, quickUrl, appId) {
        const overlay = ensureOverlayContainers();
        if (!overlay) {
            return;
        }
        const requestId = ++state.popoverRequestId;
        overlay.popoverRoot.innerHTML = "";
        const popover = document.createElement("div");
        popover.className = "popover";
        popover.setAttribute("aria-busy", "true");
        overlay.popoverRoot.appendChild(popover);
        state.popover = popover;
        state.anchorEl = row;
        showPopoverSkeleton(popover);
        positionPopover(row, popover);

        fetch(`${quickUrl}?cb=${Date.now()}`, { credentials: "same-origin", cache: "no-store" })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Quick view failed: ${response.status}`);
                }
                return response.text();
            })
            .then((html) => {
                if (requestId !== state.popoverRequestId) {
                    return;
                }
                popover.innerHTML = html;
                popover.removeAttribute("aria-busy");
                const editor = popover.querySelector("[data-app-id]");
                if (editor) {
                    setActiveEditor(editor, "popover");
                }
                positionPopover(row, popover);
            })
            .catch(() => {
                if (requestId !== state.popoverRequestId) {
                    return;
                }
                popover.innerHTML = `
                    <div class="popover-card">
                        <div class="popover-title">Unable to load</div>
                        <div class="text-subtle">Please try again.</div>
                    </div>
                `.trim();
                popover.removeAttribute("aria-busy");
            });
    }

    function trapFocus(modalEl) {
        if (!modalEl) {
            return;
        }
        const focusables = modalEl.querySelectorAll(
            "a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])"
        );
        if (!focusables.length) {
            return;
        }
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        state.focusTrapHandler = (event) => {
            if (event.key !== "Tab") {
                return;
            }
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        };
        modalEl.addEventListener("keydown", state.focusTrapHandler);
        first.focus();
    }

    function openModal(url, appId, mode) {
        const overlay = ensureOverlayContainers();
        if (!overlay) {
            return;
        }
        body.classList.add("modal-open");
        const requestId = ++state.modalRequestId;
        overlay.modalRoot.classList.add("is-open");
        overlay.modalBackdrop.hidden = false;
        overlay.modalRoot.dataset.mode = mode || "full";
        showModalSkeleton(overlay.modalRoot);

        fetch(`${url}?cb=${Date.now()}`, { credentials: "same-origin", cache: "no-store" })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Editor load failed: ${response.status}`);
                }
                return response.text();
            })
            .then((html) => {
                if (requestId !== state.modalRequestId) {
                    return;
                }
                if (mode === "quick") {
                    overlay.modalRoot.innerHTML = `
                        <div class="modal-sheet modal-sheet--quick">
                            ${html}
                        </div>
                    `.trim();
                } else {
                    overlay.modalRoot.innerHTML = `
                        <div class="modal-sheet">
                            ${html}
                        </div>
                    `.trim();
                }
                state.modal = overlay.modalRoot.querySelector(".modal-sheet");
                const editor = overlay.modalRoot.querySelector("[data-app-id]");
                if (editor) {
                    setActiveEditor(editor, "modal");
                }
                if (mode !== "quick") {
                    trapFocus(overlay.modalRoot);
                }
            })
            .catch(() => {
                if (requestId !== state.modalRequestId) {
                    return;
                }
                overlay.modalRoot.innerHTML = `
                    <div class="modal-sheet">
                        <div class="modal-panel">
                            <div class="modal-header">
                                <div class="modal-title">Unable to load editor</div>
                            </div>
                            <div class="modal-body text-subtle">Please try again.</div>
                        </div>
                    </div>
                `.trim();
            });
    }

    function openQuickForRow(row) {
        if (!row) {
            return;
        }
        const appId = row.dataset.appId;
        const quickUrl = row.dataset.quickUrl;
        if (!appId || !quickUrl) {
            return;
        }
        if (state.activeMode === "modal") {
            closeModal();
        }
        if (state.activeMode === "popover") {
            closePopover(false);
        }
        state.lastFocused = row;
        setSelectedRow(appId);
        updateSelectedParam(appId);
        if (isMobile()) {
            openModal(quickUrl, appId, "quick");
            return;
        }
        openPopover(row, quickUrl, appId);
    }

    function openFullEditorFromActive() {
        const editor = state.activeEditor;
        if (!editor) {
            return;
        }
        const editUrl = editor.dataset.editUrl;
        const appId = editor.dataset.appId;
        if (!editUrl || !appId) {
            return;
        }
        closePopover(false);
        openModal(editUrl, appId, "full");
    }

    function updateTopbarHeight() {
        const topbar = document.querySelector(".topbar");
        if (!topbar) {
            return;
        }
        const rect = topbar.getBoundingClientRect();
        root.style.setProperty("--topbar-h", `${rect.height}px`);
    }

    function initSidebarToggle() {
        const STORAGE_KEY = "jobtracker.sidebar";
        const toggle = document.getElementById("sidebarToggle");
        if (!toggle) {
            return;
        }

        function apply(stateValue) {
            if (stateValue === "collapsed") {
                root.classList.add("sidebar-collapsed");
            } else {
                root.classList.remove("sidebar-collapsed");
            }
        }

        const stored = localStorage.getItem(STORAGE_KEY);
        apply(stored || "open");

        toggle.addEventListener("click", () => {
            if (isMobile()) {
                body.classList.toggle("sidebar-open");
                toggle.setAttribute("aria-expanded", body.classList.contains("sidebar-open"));
                return;
            }
            const isCollapsed = root.classList.toggle("sidebar-collapsed");
            localStorage.setItem(STORAGE_KEY, isCollapsed ? "collapsed" : "open");
        });

        mobileQuery.addEventListener("change", () => {
            body.classList.remove("sidebar-open");
            toggle.setAttribute("aria-expanded", "false");
        });
    }

    function initUserMenu() {
        const menuButton = document.getElementById("userMenuButton");
        const menu = document.getElementById("userMenu");
        if (!menuButton || !menu) {
            return;
        }
        function closeMenu() {
            menu.hidden = true;
            menuButton.setAttribute("aria-expanded", "false");
        }
        function toggleMenu() {
            const isOpen = !menu.hidden;
            menu.hidden = isOpen;
            menuButton.setAttribute("aria-expanded", String(!isOpen));
        }
        menuButton.addEventListener("click", (event) => {
            event.stopPropagation();
            toggleMenu();
        });
        document.addEventListener("click", (event) => {
            if (!menu.contains(event.target) && !menuButton.contains(event.target)) {
                closeMenu();
            }
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeMenu();
            }
        });
    }

    function initKanban() {
        const kanban = document.querySelector("[data-kanban]");
        if (!kanban) {
            return;
        }
        let draggedCard = null;
        let draggedFromColumn = null;
        let draggedFromList = null;

        function updateColumnCount(column, delta) {
            if (!column) {
                return;
            }
            const badge = column.querySelector("[data-column-count]");
            if (!badge) {
                return;
            }
            const current = parseInt(badge.textContent || "0", 10);
            const next = Math.max(current + delta, 0);
            badge.textContent = `${next}`;
        }

        kanban.addEventListener("dragstart", (event) => {
            const card = event.target.closest(".kanban-card");
            if (!card) {
                return;
            }
            draggedCard = card;
            draggedFromColumn = card.closest(".kanban-column");
            draggedFromList = card.closest(".kanban-cards");
            card.classList.add("is-dragging");
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", card.dataset.appId || "");
        });

        kanban.addEventListener("dragend", (event) => {
            const card = event.target.closest(".kanban-card");
            if (card) {
                card.classList.remove("is-dragging");
            }
            draggedCard = null;
            draggedFromColumn = null;
            draggedFromList = null;
        });

        kanban.addEventListener("dragover", (event) => {
            const column = event.target.closest(".kanban-cards");
            if (column) {
                event.preventDefault();
            }
        });

        kanban.addEventListener("drop", (event) => {
            const column = event.target.closest(".kanban-column");
            const targetList = event.target.closest(".kanban-cards");
            if (!column || !targetList || !draggedCard) {
                return;
            }
            event.preventDefault();
            const newStatus = column.dataset.status;
            const originalList = draggedFromList;
            const originalColumn = draggedFromColumn;
            targetList.prepend(draggedCard);
            updateColumnCount(originalColumn, -1);
            updateColumnCount(column, 1);
            sendPatch(draggedCard.dataset.patchUrl, { status: newStatus })
                .then((data) => {
                    applyPatchUpdate(data.application, getRowById(data.application.id));
                    setLastSavedAt(data.saved_at);
                    const moveSelect = draggedCard.querySelector("[data-move-select]");
                    if (moveSelect) {
                        moveSelect.value = data.application.status;
                        moveSelect.dataset.prevValue = data.application.status;
                    }
                })
                .catch(() => {
                    if (originalList) {
                        originalList.prepend(draggedCard);
                        updateColumnCount(originalColumn, 1);
                        updateColumnCount(column, -1);
                    }
                    showToast("Move failed. Status reverted.");
                });
        });

        kanban.addEventListener("change", (event) => {
            const moveSelect = event.target.closest("[data-move-select]");
            if (!moveSelect) {
                return;
            }
            const card = moveSelect.closest(".kanban-card");
            const newStatus = moveSelect.value;
            const previousStatus = moveSelect.dataset.prevValue || newStatus;
            const originalColumn = card.closest(".kanban-column");
            const targetColumn = kanban.querySelector(`.kanban-column[data-status="${newStatus}"]`);
            const targetList = targetColumn ? targetColumn.querySelector(".kanban-cards") : null;

            if (targetList && targetList !== card.parentElement) {
                targetList.prepend(card);
                updateColumnCount(originalColumn, -1);
                updateColumnCount(targetColumn, 1);
            }
            sendPatch(card.dataset.patchUrl, { status: newStatus })
                .then((data) => {
                    applyPatchUpdate(data.application, getRowById(data.application.id));
                    setLastSavedAt(data.saved_at);
                    moveSelect.dataset.prevValue = data.application.status;
                })
                .catch(() => {
                    moveSelect.value = previousStatus;
                    if (originalColumn && originalColumn !== card.closest(".kanban-column")) {
                        const originalList = originalColumn.querySelector(".kanban-cards");
                        if (originalList) {
                            originalList.prepend(card);
                            updateColumnCount(originalColumn, 1);
                            updateColumnCount(targetColumn, -1);
                        }
                    }
                    showToast("Move failed. Try again.");
                });
        });
    }

    document.addEventListener("click", (event) => {
        const openEditor = event.target.closest("[data-open-editor]");
        if (openEditor) {
            event.preventDefault();
            openFullEditorFromActive();
            return;
        }

        const closeBtn = event.target.closest("[data-popover-close], [data-modal-close]");
        if (closeBtn) {
            if (state.activeMode === "modal") {
                closeModal();
            } else {
                closePopover(true);
            }
            return;
        }

        const clearButton = event.target.closest("[data-followup-clear]");
        if (clearButton) {
            const editor = state.activeEditor;
            const input = editor ? editor.querySelector("[data-autosave='follow_up_on']") : null;
            const previousValue = input ? input.value : "";
            if (input) {
                input.value = "";
                state.lastFieldSnapshot.follow_up_on = "";
                clearFieldErrors(editor, "follow_up_on");
            }
            state.lastUndoCandidate = {
                field: "follow_up_on",
                fromValue: previousValue,
                toValue: "",
            };
            setSaveStatus("saving");
            queueImmediateSave({ follow_up_on: "" });
            return;
        }

        const saveButton = event.target.closest("[data-save-status]");
        if (saveButton && saveButton.classList.contains("is-error")) {
            if (state.lastFailedPayload) {
                state.pendingPayload = { ...state.lastFailedPayload };
                state.lastFailedPayload = null;
                setSaveStatus("saving");
                flushSave();
            }
            return;
        }

        if (isInteractive(event.target)) {
            return;
        }
        const row = event.target.closest(".app-row");
        if (row) {
            openQuickForRow(row);
        }
    });

    document.addEventListener("mousedown", (event) => {
        if (state.popover && !state.popover.contains(event.target)) {
            const row = event.target.closest(".app-row");
            if (!row) {
                closePopover(true);
            }
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            if (state.activeMode === "modal") {
                closeModal();
            } else if (state.activeMode === "popover") {
                closePopover(true);
            }
        }
        if (event.key === "Enter" || event.key === " ") {
            if (isInteractive(event.target)) {
                return;
            }
            const row = event.target.closest(".app-row");
            if (row) {
                event.preventDefault();
                openQuickForRow(row);
            }
        }
    });

    document.addEventListener("input", (event) => {
        const editor = state.activeEditor;
        if (!editor || !editor.contains(event.target)) {
            return;
        }
        if (!event.target.matches("[data-autosave]")) {
            return;
        }
        if (event.target.type === "date") {
            return;
        }
        const field = event.target.dataset.autosave;
        state.pendingPayload[field] = event.target.value;
        clearFieldErrors(editor, field);
        scheduleSave();
    });

    document.addEventListener("change", (event) => {
        const editor = state.activeEditor;
        if (editor && editor.contains(event.target) && event.target.matches("[data-autosave]")) {
            const field = event.target.dataset.autosave;
            const value = event.target.value;
            const previousValue = state.lastFieldSnapshot[field] || "";
            state.lastFieldSnapshot[field] = value;
            clearFieldErrors(editor, field);

            if (field === "status" || field === "follow_up_on") {
                state.lastUndoCandidate = {
                    field,
                    fromValue: previousValue,
                    toValue: value,
                };
                setSaveStatus("saving");
                queueImmediateSave({ [field]: value });
                return;
            }
            state.pendingPayload[field] = value;
            scheduleSave();
        }

        const followupItem = event.target.closest("[data-followup-id]");
        if (followupItem) {
            const followupId = followupItem.dataset.followupId;
            const payload = {};
            if (event.target.matches("[data-followup-complete]")) {
                payload.is_completed = event.target.checked;
            }
            if (event.target.matches("[data-followup-due]")) {
                payload.due_on = event.target.value;
            }
            if (event.target.matches("[data-followup-note]")) {
                payload.note = event.target.value;
            }
            if (Object.keys(payload).length) {
                sendFollowupUpdate(followupId, payload)
                    .then((data) => {
                        if (data.followup.is_completed) {
                            followupItem.classList.add("is-complete");
                        } else {
                            followupItem.classList.remove("is-complete");
                        }
                    })
                    .catch(() => {
                        showToast("Follow-up update failed.");
                    });
            }
        }

        const quickToggle = event.target.closest("[data-quick-profile]");
        if (quickToggle && event.target.type === "checkbox") {
            const form = quickToggle.closest("form");
            if (!form) {
                return;
            }
            const csrfToken = getCookie("csrftoken");
            const formData = new FormData(form);
            fetch(form.action, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: formData,
            })
                .then((response) => response.json())
                .then((data) => {
                    if (!data.ok) {
                        throw new Error("Profile update failed.");
                    }
                })
                .catch(() => {
                    showToast("Unable to update reminders.");
                });
        }
    });

    document.addEventListener("submit", (event) => {
        const quickAddForm = event.target.closest("[data-quick-add]");
        if (quickAddForm) {
            event.preventDefault();
            const csrfToken = getCookie("csrftoken");
            const formData = new FormData(quickAddForm);
            fetch(quickAddForm.action, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: formData,
            })
                .then((response) => response.json())
                .then((data) => {
                    if (!data.ok) {
                        throw new Error(data.error || "Quick add failed.");
                    }
                    const url = new URL(window.location.href);
                    url.searchParams.set("selected", data.id);
                    window.location.href = url.toString();
                })
                .catch(() => {
                    showToast("Quick add failed. Check the fields and try again.");
                });
            return;
        }

        const followupForm = event.target.closest("[data-followup-create]");
        if (followupForm) {
            event.preventDefault();
            const editor = state.activeEditor;
            const followupUrl = editor ? editor.dataset.followupUrl : "";
            if (!followupUrl) {
                return;
            }
            const csrfToken = getCookie("csrftoken");
            const dueOn = followupForm.querySelector("input[name='due_on']").value;
            const note = followupForm.querySelector("input[name='note']").value;
            fetch(followupUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/json;charset=UTF-8",
                },
                body: JSON.stringify({ due_on: dueOn, note: note }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (!data.ok) {
                        throw new Error(data.error || "Follow-up create failed.");
                    }
                    const list = editor.querySelector("[data-followup-list]");
                    if (list) {
                        const placeholder = list.querySelector(".text-subtle");
                        if (placeholder) {
                            placeholder.remove();
                        }
                        list.appendChild(renderFollowupItem(data.followup));
                    }
                    followupForm.reset();
                })
                .catch(() => {
                    showToast("Unable to add follow-up.");
                });
        }
    });

    function handleSelectedParamChange() {
        const selected = new URLSearchParams(window.location.search).get("selected");
        if (selected && selected !== state.selectedId) {
            const row = getRowById(selected);
            if (row) {
                openQuickForRow(row);
            } else {
                updateSelectedParam(null);
            }
        }
        if (!selected && state.selectedId) {
            closePopover(true);
            closeModal();
        }
    }

    window.addEventListener("popstate", handleSelectedParamChange);
    window.addEventListener("resize", () => {
        updateTopbarHeight();
        if (state.popover && state.anchorEl) {
            positionPopover(state.anchorEl, state.popover);
        }
    });
    window.addEventListener("scroll", () => {
        if (state.popover && state.anchorEl) {
            positionPopover(state.anchorEl, state.popover);
        }
    }, true);

    initSidebarToggle();
    initUserMenu();
    initKanban();
    updateTopbarHeight();

    const selected = new URLSearchParams(window.location.search).get("selected");
    if (selected) {
        const row = getRowById(selected);
        if (row) {
            openQuickForRow(row);
        } else {
            updateSelectedParam(null);
        }
    }
})();
