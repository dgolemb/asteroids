(() => {
    const STICK_RADIUS_RATIO = 0.2;
    const STICK_DEADZONE_RATIO = 0.12;
    const TAP_MAX_MILLISECONDS = 300;
    const TAP_MAX_MOVEMENT_PIXELS = 20;
    const RESIZE_DEBOUNCE_MILLISECONDS = 200;

    const root = document.documentElement;
    const touchDevice = navigator.maxTouchPoints > 0 && window.matchMedia("(pointer: coarse)").matches;

    const state = {
        available: touchDevice,
        blocked: false,
        stick_x: 0,
        stick_y: 0,
        tap_serial: 0,
        tap_x: 0,
        tap_y: 0,
    };
    window.touch_state = state;

    if (!touchDevice) {
        return;
    }

    root.classList.add("touch", "immersive");

    let stickId = null;
    const origin = { x: 0, y: 0 };
    const pending = new Map();
    let resizeTimer = 0;

    function toGameSpace(clientX, clientY) {
        const canvas = document.getElementById("canvas");
        const rect = canvas.getBoundingClientRect();
        if (!rect.width || !rect.height) {
            return { x: clientX, y: clientY };
        }
        return {
            x: ((clientX - rect.left) / rect.width) * canvas.width,
            y: ((clientY - rect.top) / rect.height) * canvas.height,
        };
    }

    function resetStick() {
        stickId = null;
        state.stick_x = 0;
        state.stick_y = 0;
    }

    function updateStick(x, y) {
        const radius = window.innerHeight * STICK_RADIUS_RATIO;
        let dx = x - origin.x;
        let dy = y - origin.y;
        const length = Math.hypot(dx, dy);
        if (length > radius) {
            origin.x = x - (dx / length) * radius;
            origin.y = y - (dy / length) * radius;
            dx = x - origin.x;
            dy = y - origin.y;
        }
        const magnitude = Math.hypot(dx, dy) / radius;
        if (magnitude < STICK_DEADZONE_RATIO) {
            state.stick_x = 0;
            state.stick_y = 0;
            return;
        }
        const scaled = (magnitude - STICK_DEADZONE_RATIO) / (1 - STICK_DEADZONE_RATIO);
        state.stick_x = (dx / (magnitude * radius)) * scaled;
        state.stick_y = (dy / (magnitude * radius)) * scaled;
    }

    function registerTap(touch) {
        const game = toGameSpace(touch.clientX, touch.clientY);
        state.tap_x = game.x;
        state.tap_y = game.y;
        state.tap_serial += 1;
    }

    function onTouchStart(event) {
        if (state.blocked) {
            return;
        }
        for (const touch of Array.from(event.changedTouches)) {
            pending.set(touch.identifier, { x: touch.clientX, y: touch.clientY, time: event.timeStamp });
            if (stickId === null && touch.clientX < window.innerWidth / 2) {
                stickId = touch.identifier;
                origin.x = touch.clientX;
                origin.y = touch.clientY;
                updateStick(touch.clientX, touch.clientY);
            }
        }
    }

    function onTouchMove(event) {
        if (root.classList.contains("immersive")) {
            event.preventDefault();
        }
        for (const touch of Array.from(event.changedTouches)) {
            if (touch.identifier === stickId) {
                updateStick(touch.clientX, touch.clientY);
            }
        }
    }

    function onTouchEnd(event) {
        for (const touch of Array.from(event.changedTouches)) {
            const started = pending.get(touch.identifier);
            pending.delete(touch.identifier);
            if (touch.identifier === stickId) {
                resetStick();
            }
            if (event.type !== "touchend" || !started || state.blocked) {
                continue;
            }
            const duration = event.timeStamp - started.time;
            const movement = Math.hypot(touch.clientX - started.x, touch.clientY - started.y);
            if (duration <= TAP_MAX_MILLISECONDS && movement <= TAP_MAX_MOVEMENT_PIXELS) {
                registerTap(touch);
            }
        }
    }

    function resizeGame() {
        if (typeof window.window_resize === "function") {
            window.window_resize();
        }
    }

    function scheduleResize() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(resizeGame, RESIZE_DEBOUNCE_MILLISECONDS);
    }

    document.addEventListener("touchstart", onTouchStart, { passive: true });
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("touchend", onTouchEnd, { passive: true });
    document.addEventListener("touchcancel", onTouchEnd, { passive: true });

    ["gesturestart", "gesturechange", "gestureend"].forEach((name) => {
        document.addEventListener(name, (event) => event.preventDefault());
    });

    window.addEventListener("resize", scheduleResize);
    window.addEventListener("orientationchange", scheduleResize);
    if (window.visualViewport) {
        window.visualViewport.addEventListener("resize", scheduleResize);
    }
})();
