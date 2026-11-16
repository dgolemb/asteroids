(() => {
    const STICK_RADIUS_RATIO = 0.2;
    const STICK_DEADZONE_RATIO = 0.12;
    const TAP_MAX_MILLISECONDS = 300;
    const TAP_MAX_MOVEMENT_PIXELS = 20;
    const RESIZE_DEBOUNCE_MILLISECONDS = 200;
    const SAFETY_POLL_MILLISECONDS = 500;

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

    root.classList.add("touch");

    const requestFullscreen = root.requestFullscreen || root.webkitRequestFullscreen;
    const scrollMode = !requestFullscreen;
    const fullscreenOverlay = createOverlay("fullscreen-overlay", "Tap to enter fullscreen");
    const swipeOverlay = createOverlay("swipe-overlay", "Swipe up to enter fullscreen");
    const rotateOverlay = createOverlay("rotate-overlay", "Rotate your device");
    const probe = scrollMode ? createMarker("viewport-probe") : null;
    if (scrollMode) {
        createMarker("scroll-spacer");
    }
    let fullscreenTried = false;
    let lastSignature = "";

    let stickId = null;
    const origin = { x: 0, y: 0 };
    const pending = new Map();
    let evaluateTimer = 0;

    function createMarker(id) {
        const element = document.createElement("div");
        element.id = id;
        document.body.appendChild(element);
        return element;
    }

    function createOverlay(id, text) {
        const element = document.createElement("div");
        element.id = id;
        element.className = "mobile-overlay";
        element.textContent = text;
        document.body.appendChild(element);
        return element;
    }

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

    function inFullscreen() {
        return Boolean(document.fullscreenElement || document.webkitFullscreenElement);
    }

    function barsCollapsed() {
        return navigator.standalone === true || window.innerHeight >= probe.offsetHeight - 2;
    }

    function evaluate() {
        const portrait = window.matchMedia("(orientation: portrait)").matches;
        const needsFullscreen = Boolean(requestFullscreen) && !inFullscreen() && !fullscreenTried && !portrait;
        const needsSwipe = scrollMode && !portrait && !barsCollapsed();
        const blocked = portrait || needsFullscreen || needsSwipe;
        const signature = [portrait, needsFullscreen, needsSwipe, window.innerWidth, window.innerHeight].join("|");
        if (signature === lastSignature) {
            return;
        }
        lastSignature = signature;
        root.classList.toggle("portrait", portrait);
        root.classList.toggle("needs-fullscreen", needsFullscreen);
        root.classList.toggle("needs-swipe", needsSwipe);
        root.classList.toggle("immersive", !blocked);
        state.blocked = blocked;
        if (blocked) {
            resetStick();
            pending.clear();
        }
        resizeGame();
    }

    function scheduleEvaluate() {
        clearTimeout(evaluateTimer);
        evaluateTimer = setTimeout(evaluate, RESIZE_DEBOUNCE_MILLISECONDS);
    }

    async function attempt(action) {
        try {
            await action();
        } catch (error) {
            return false;
        }
        return true;
    }

    async function enterFullscreen() {
        fullscreenTried = true;
        const entered = await attempt(() => requestFullscreen.call(root, { navigationUI: "hide" }));
        if (entered && screen.orientation && screen.orientation.lock) {
            await attempt(() => screen.orientation.lock("landscape"));
        }
        evaluate();
    }

    fullscreenOverlay.addEventListener("click", enterFullscreen);
    document.addEventListener("fullscreenchange", evaluate);
    document.addEventListener("webkitfullscreenchange", evaluate);

    document.addEventListener("touchstart", onTouchStart, { passive: true });
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("touchend", onTouchEnd, { passive: true });
    document.addEventListener("touchcancel", onTouchEnd, { passive: true });

    ["gesturestart", "gesturechange", "gestureend"].forEach((name) => {
        document.addEventListener(name, (event) => event.preventDefault());
    });

    rotateOverlay.addEventListener("click", () => {
        if (requestFullscreen && !fullscreenTried && !inFullscreen()) {
            enterFullscreen();
        }
    });

    window.addEventListener("resize", scheduleEvaluate);
    window.addEventListener("orientationchange", scheduleEvaluate);
    if (window.visualViewport) {
        window.visualViewport.addEventListener("resize", scheduleEvaluate);
    }
    if (scrollMode) {
        window.addEventListener("scroll", scheduleEvaluate);
        setInterval(evaluate, SAFETY_POLL_MILLISECONDS);
    }

    evaluate();
})();
