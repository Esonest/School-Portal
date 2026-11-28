(function () {
    'use strict';

    const root = document.documentElement;
    const androidUser = document.getElementById('techcenter-android-user');

const currentRole = androidUser?.dataset.role || '';
const currentSchool = androidUser?.dataset.schoolId || '';


    // This entire feature is restricted to the Android app.
    if (!root.classList.contains('techcenter-android-app')) return;

    const toolbar = document.getElementById('android-display-toolbar');

    /* ======================================
   DARK MODE
====================================== */

const darkButton = document.getElementById('android-dark-toggle');
const darkIcon = document.getElementById('android-dark-icon');
const darkLabel = document.getElementById('android-dark-label');

let isDark = localStorage.getItem('tc_android_dark_mode') === 'true';

function applyDarkMode() {
    root.classList.toggle('tc-dark', isDark);

    if (darkIcon) {
        darkIcon.textContent = isDark ? '☀️' : '🌙';
    }

    if (darkLabel) {
        darkLabel.textContent = isDark ? 'Light' : 'Dark';
    }

    localStorage.setItem('tc_android_dark_mode', String(isDark));
}

if (darkButton) {
    darkButton.addEventListener('click', function () {
        isDark = !isDark;
        applyDarkMode();
    });
}

applyDarkMode();


    /* ======================================
       PAGE ZOOM: 80% TO 150%
    ====================================== */

    const zoomContent =
    document.getElementById('android-zoom-content');

const isLoginPage = document.body.classList.contains('login-layout');
    const zoomIn = document.getElementById('android-zoom-in');
    const zoomOut = document.getElementById('android-zoom-out');
    const zoomLevel = document.getElementById('android-zoom-level');

    let zoom = parseFloat(localStorage.getItem('tc_android_zoom') || '1');

    if (!Number.isFinite(zoom)) zoom = 1;

    function applyZoom() {
        zoom = Math.max(0.8, Math.min(1.5, zoom));

        if (zoomContent && !isLoginPage) {
    zoomContent.style.zoom = String(zoom);
}

       if (zoomLevel) {
    zoomLevel.textContent = Math.round(zoom * 100) + '%';
}

        localStorage.setItem('tc_android_zoom', String(zoom));
    }

   if (zoomIn) {
    zoomIn.addEventListener('click', function () {
        zoom = Math.round((zoom + 0.1) * 10) / 10;
        applyZoom();
    });
}

if (zoomOut) {
    zoomOut.addEventListener('click', function () {
        zoom = Math.round((zoom - 0.1) * 10) / 10;
        applyZoom();
    });
}

    applyZoom();


    /* ======================================
       NOTIFICATION STORAGE
    ====================================== */

    const STORAGE_KEY =
    'tc_android_notification_history_' +
    currentSchool + '_' +
    currentRole;
    
    const notificationButton = document.getElementById('android-notification-button');
    const notificationCount = document.getElementById('android-notification-count');

    const overlay = document.getElementById('android-notification-overlay');
    const closeButton = document.getElementById('android-notification-close');

    const list = document.getElementById('android-notification-list');
    const empty = document.getElementById('android-notification-empty');
    const summary = document.getElementById('android-notification-summary');

    const markAllButton = document.getElementById('android-mark-all-read');
    const clearButton = document.getElementById('android-clear-notifications');

    const detail = document.getElementById('android-notification-detail');
    const detailTitle = document.getElementById('android-detail-title');
    const detailDate = document.getElementById('android-detail-date');
    const detailMessage = document.getElementById('android-detail-message');
    const detailLink = document.getElementById('android-detail-link');
    const backButton = document.getElementById('android-notification-back');

    function loadNotifications() {
        try {
            const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            return Array.isArray(data) ? data : [];
        } catch (error) {
            console.error('Unable to read notification history:', error);
            return [];
        }
    }

    function saveNotifications(items) {
        // Keep the latest 200 notifications.
        items = items.slice(0, 200);

        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
        } catch (error) {
            console.error('Unable to save notification history:', error);
        }
    }

    function escapeNotificationText(value) {
        return String(value == null ? '' : value);
    }

    function updateNotificationCount() {
    const items = loadNotifications();
    const unread = items.filter(item => !item.read).length;

    if (notificationCount) {
        notificationCount.textContent = unread > 99 ? '99+' : String(unread);
        notificationCount.hidden = unread === 0;
    }

    if (summary) {
        summary.textContent =
            items.length + ' saved notification' +
            (items.length === 1 ? '' : 's') +
            ' · ' + unread + ' unread';
    }
}

    function addNotification(data) {
        if (!data || typeof data !== 'object') return;

        const title = escapeNotificationText(data.title || data.subject || 'TECHCENTER Notification').trim();
        const message = escapeNotificationText(data.message || data.body || data.text || '').trim();

        if (!message && !title) return;

        const items = loadNotifications();

        // Avoid duplicate notifications when the same event is delivered again.
        if (data.id && items.some(item => item.sourceId === String(data.id))) {
            return;
        }

        const notification = {
            id: 'tc_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9),
            sourceId: data.id ? String(data.id) : '',
            title: title,
            message: message,
            date: data.date || data.timestamp || new Date().toISOString(),
            url: data.url || '',
            type: data.type || 'general',
            read: false
        };

        items.unshift(notification);
        saveNotifications(items);
        updateNotificationCount();

        // Refresh the inbox if it is already open.
        if (overlay && !overlay.hidden) {
    renderNotificationList();
}
    }

    function formatNotificationDate(value) {
        const date = new Date(value);

        if (Number.isNaN(date.getTime())) return '';

        return date.toLocaleString();
    }

    function renderNotificationList() {
        const items = loadNotifications();

        list.replaceChildren();
        detail.hidden = true;
        list.hidden = false;
        empty.hidden = items.length > 0;

        items.forEach(function (item) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'android-notification-item' +
                (item.read ? '' : ' unread');

            const content = document.createElement('div');
            content.className = 'android-notification-item-content';

            const title = document.createElement('div');
            title.className = 'android-notification-item-title';
            title.textContent = item.title;

            const message = document.createElement('div');
            message.className = 'android-notification-item-message';
            message.textContent = item.message;

            const date = document.createElement('div');
            date.className = 'android-notification-item-date';
            date.textContent = formatNotificationDate(item.date);

            content.append(title, message, date);
            button.appendChild(content);

            if (!item.read) {
                const dot = document.createElement('span');
                dot.className = 'android-notification-unread-dot';
                button.appendChild(dot);
            }

            button.addEventListener('click', function () {
                openNotification(item.id);
            });

            list.appendChild(button);
        });

        updateNotificationCount();
    }

    function openNotification(id) {
        const items = loadNotifications();
        const item = items.find(notification => notification.id === id);

        if (!item) return;

        item.read = true;
        saveNotifications(items);

        list.hidden = true;
        empty.hidden = true;
        detail.hidden = false;

        detailTitle.textContent = item.title;
        detailDate.textContent = formatNotificationDate(item.date);
        detailMessage.textContent = item.message;

        detailLink.hidden = true;
        detailLink.removeAttribute('href');

        // Only allow links back to this website.
        if (item.url) {
            try {
                const safeUrl = new URL(item.url, window.location.origin);

                if (safeUrl.origin === window.location.origin) {
                    detailLink.href = safeUrl.href;
                    detailLink.hidden = false;
                }
            } catch (error) {
                console.warn('Invalid notification URL.');
            }
        }

        updateNotificationCount();
    }

    function openInbox() {
    if (!overlay) return;

    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    renderNotificationList();
}

function closeInbox() {
    if (!overlay) return;

    overlay.hidden = true;
    document.body.style.overflow = '';
}

    if (notificationButton) {
    notificationButton.addEventListener('click', openInbox);
}

if (closeButton) {
    closeButton.addEventListener('click', closeInbox);
}

if (overlay) {
    overlay.addEventListener('click', function (event) {
        if (event.target === overlay) closeInbox();
    });
}

if (backButton) {
    backButton.addEventListener('click', renderNotificationList);
}

    if (markAllButton) {
    markAllButton.addEventListener('click', function () {
        const items = loadNotifications();

        items.forEach(item => {
            item.read = true;
        });

        saveNotifications(items);
        renderNotificationList();
    });
}

if (clearButton) {
    clearButton.addEventListener('click', function () {
        if (!confirm('Clear all saved notifications? This cannot be undone.')) {
            return;
        }

        saveNotifications([]);
        renderNotificationList();
    });
}

    function handleTechcenterNotification(data) {
    if (!data) return;

    addNotification(data);
    showPushNotification(data);
}

window.addEventListener('techcenter:notification', function (event) {
    handleTechcenterNotification(event.detail);
});

// Mark the notification handler as ready.
window.__tcToolsReady = true;

// Process notifications that arrived before this script loaded.
const pendingNotifications = window.__tcPendingNotifications || [];

window.__tcPendingNotifications = [];

pendingNotifications.forEach(function (data) {
    handleTechcenterNotification(data);
});

    // Simple helper for existing portal scripts.
    window.TechcenterNotifications = {
        add: addNotification,
        open: openInbox,
        refresh: updateNotificationCount
    };

    /* ======================================
       SAVE DJANGO FLASH MESSAGES
    ====================================== */

    document.querySelectorAll('#flash-container .flash-message').forEach(function (element) {
        const message = element.textContent.trim();

        if (!message) return;

        addNotification({
            title: 'Portal notification',
            message: message,
            type: 'django-message'
        });
    });

    updateNotificationCount();

})();



/* ==========================================
   TECHCENTER ROLE-BASED BOTTOM NAVIGATION
   BASE TEMPLATE - ANDROID APP ONLY
========================================== */

(function () {
    'use strict';

    const root = document.documentElement;

    // Android app only.
    if (!root.classList.contains('techcenter-android-app')) return;

    const userElement = document.getElementById('techcenter-android-user');
    const navigation = document.getElementById('techcenter-app-navigation');

    // Do not display navigation for unauthenticated users.
    if (!userElement || !navigation) return;

    const role = userElement.dataset.role || '';
    const schoolId = userElement.dataset.schoolId || '';

    const schoolFallback = '/portal-selection/';

    const groups = {
        student: [
            ['⌂', 'Dashboard', '/students/'],
            ['▤', 'My Results', '/results/student/portal/'],
            ['▣', 'Assignments', '/assignments/'],
            ['▧', 'Lesson Notes', '/notes/'],
            ['✎', 'CBT Exams', '/cbt/'],
            ['₦', 'Payments', '/finance/student/']
        ],

        teacher: [
            ['⌂', 'Dashboard', '/teachers/dashboard/'],
            ['▤', 'Results', '/teachers/results/'],
            ['▣', 'Assignments', '/assignments/'],
            ['◷', 'Attendance', schoolId
                ? '/school_admin/' + schoolId + '/attendance/'
                : schoolFallback],
            ['✎', 'CBT Exams', '/school_admin/'],
            ['▧', 'Lesson Notes', '/notes/'],
            ['◎', 'Live Classes', '/liveclass/']
        ],

        schooladmin: [
            ['⌂', 'Dashboard', schoolId
                ? '/school_admin/school_admin/' + schoolId + '/'
                : schoolFallback],
            ['✎', 'Bulk Scores', schoolId
                ? '/results/school/' + schoolId + '/scores/'
                : schoolFallback],
            ['◈', 'Psychomotor & Affective', schoolId
                ? '/results/bulk_psycho_affective/' + schoolId + '/'
                : schoolFallback],
            ['⇩', 'Bulk Results Download', schoolId
                ? '/results/school/' + schoolId + '/bulk-results/select/'
                : schoolFallback],
            ['♙', 'Students', schoolId
                ? '/school_admin/' + schoolId + '/'
                : schoolFallback],
            ['♟', 'Teachers', schoolId
                ? '/school_admin/' + schoolId + '/teachers/'
                : schoolFallback],
            ['▦', 'Classes', schoolId
                ? '/school_admin/' + schoolId + '/classes/'
                : schoolFallback],
            ['◷', 'Attendance', schoolId
                ? '/school_admin/' + schoolId + '/attendance/'
                : schoolFallback],
            ['✎', 'CBT', schoolId
                ? '/school_admin/admin/' + schoolId + '/'
                : schoolFallback],
            ['▣', 'Assignments', '/assignments/'],
            ['▧', 'Lesson Notes', '/notes/'],
            ['₦', 'Finance', '/finance/']
        ],

        accountant: [
            ['⌂', 'Dashboard', '/finance/'],
            ['▤', 'Invoices', '/finance/invoices/'],
            ['₦', 'Payments', '/finance/payments/'],
            ['＋', 'Create Invoices', '/finance/invoice/create/'],
            ['▧', 'Expenses', '/finance/expenses/']
        ],

        superadmin: [
            ['⌂', 'Dashboard', '/portal-selection/']
        ]
    };

    const menuItems = groups[role];

    if (!menuItems) return;

    // Build the navigation container.
    navigation.replaceChildren();

    const popup = document.createElement('div');
    popup.id = 'tc-role-nav-popup';

    const bottomItems = document.createElement('div');
    bottomItems.id = 'tc-role-nav-items';

    
function createNavIcon(name) {
    const paths = {
        home: 'M3 10.5 12 3l9 7.5M5.5 9v11h13V9M9 20v-6h6v6',
        results: 'M5 3h14v18H5zM8 8h8M8 12h8M8 16h5',
        assignments: 'M8 4h8M9 3h6v3H9zM6 5H4v16h16V5h-2M8 11h8M8 15h8',
        notes: 'M5 3h14v18H5zM8 8h8M8 12h8M8 16h5',
        exam: 'M4 4h16v16H4zM8 8h8M8 12h8M8 16h4',
        payment: 'M12 2v20M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
        attendance: 'M8 3v3M16 3v3M4 8h16M5 5h14v16H5zM8 13l2.5 2.5L16 10',
        download: 'M12 3v12M7 10l5 5 5-5M4 20h16',
        students: 'M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M10 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
        teachers: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8M4 21a8 8 0 0 1 16 0M18 8h4M20 6v4',
        classes: 'M3 4h18v16H3zM3 9h18M9 9v11M15 9v11',
        live: 'M3 8h18v12H3zM8 8l2-4h4l2 4M10 14l5 3-5 3z',
        profile: 'M20 21a8 8 0 0 0-16 0M12 13a4 4 0 1 0 0-8 4 4 0 0 0 0 8',
        settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-1.7 2.94-.08-.02a1.7 1.7 0 0 0-1.7.49l-.06.06h-3.4l-.04-.08a1.7 1.7 0 0 0-1.48-.98 1.7 1.7 0 0 0-1.48.98l-.04.08h-3.4l-.06-.06a1.7 1.7 0 0 0-1.7-.49l-.08.02-1.7-2.94.06-.06A1.7 1.7 0 0 0 3.4 15l-.08-.04v-3.4l.08-.04a1.7 1.7 0 0 0 .98-1.48 1.7 1.7 0 0 0-.98-1.48l-.08-.04V5.12l.08-.04a1.7 1.7 0 0 0 1.48-.98l.04-.08h3.4l.04.08a1.7 1.7 0 0 0 1.48.98 1.7 1.7 0 0 0 1.48-.98l.04-.08h3.4l.06.06a1.7 1.7 0 0 0 1.7.49l.08-.02 1.7 2.94-.06.06A1.7 1.7 0 0 0 19.4 9l.08.04v3.4z',
        logout: 'M10 17l5-5-5-5M15 12H3M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7',
        finance: 'M3 6h18v13H3zM3 10h18M7 15h4',
        plus: 'M12 5v14M5 12h14',
        psychomotor: 'M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6 5.6 18.4',
        generic: 'M4 4h16v16H4zM8 8h8M8 12h8M8 16h5'
    };

    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');

    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.8');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');

    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('d', paths[name] || paths.generic);
    svg.appendChild(path);

    return svg;
}

function getNavIconName(label) {
    const names = {
        'Dashboard': 'home',
        'My Results': 'results',
        'Results': 'results',
        'Assignments': 'assignments',
        'Lesson Notes': 'notes',
        'CBT Exams': 'exam',
        'CBT': 'exam',
        'Payments': 'payment',
        'Invoices': 'results',
        'Create Invoices': 'plus',
        'Expenses': 'finance',
        'Finance': 'finance',
        'Attendance': 'attendance',
        'Bulk Scores': 'results',
        'Psychomotor & Affective': 'psychomotor',
        'Bulk Results Download': 'download',
        'Students': 'students',
        'Teachers': 'teachers',
        'Classes': 'classes',
        'Live Classes': 'live',
        'Profile': 'profile',
        'Logout': 'logout',
        'Settings': 'settings'
    };

    return names[label] || 'generic';
}

function createLink(item, popupLink) {
    const link = document.createElement('a');

    link.href = item[2];
    link.className = popupLink
        ? 'tc-role-popup-link'
        : 'tc-role-nav-link';

    const icon = document.createElement('span');
    icon.className = popupLink
        ? 'tc-role-popup-icon'
        : 'tc-role-nav-icon';

    icon.appendChild(createNavIcon(getNavIconName(item[1])));

    const label = document.createElement('span');
    label.className = popupLink
        ? 'tc-role-popup-label'
        : 'tc-role-nav-label';
    label.textContent = item[1];

    link.append(icon, label);

    return link;
}

    // First four role-specific links appear in the bottom bar.
    menuItems.slice(0, 4).forEach(function (item) {
        bottomItems.appendChild(createLink(item, false));
    });

    // Remaining role-specific links appear in the Settings popup.
    menuItems.slice(4).forEach(function (item) {
        popup.appendChild(createLink(item, true));
    });

    // Profile link.
    const profileLink = createLink(
        ['♙', 'Profile', '/students/profile/'],
        true
    );

    if (popup.children.length) {
        const divider = document.createElement('div');
        divider.className = 'tc-role-popup-divider';
        popup.appendChild(divider);
    }

    popup.appendChild(profileLink);

    // Logout link with native Android confirmation.
const logoutLink = createLink(
    ['⇥', 'Logout', '/logout/'],
    true
);

logoutLink.classList.add('tc-role-logout');

logoutLink.addEventListener('click', function (event) {
    event.preventDefault();

    const confirmed = window.confirm(
        'Are you sure you want to log out of your TECHCENTER account?'
    );

    if (confirmed) {
        window.location.href = logoutLink.href;
    }
});

popup.appendChild(logoutLink);

    // Settings button.
    const settingsButton = document.createElement('button');
    settingsButton.type = 'button';
    settingsButton.className = 'tc-role-nav-settings';
    settingsButton.setAttribute('aria-label', 'Open Settings menu');
    settingsButton.setAttribute('aria-expanded', 'false');

    const settingsIcon = document.createElement('span');
settingsIcon.className = 'tc-role-nav-icon';
settingsIcon.appendChild(createNavIcon('settings'));

    const settingsLabel = document.createElement('span');
    settingsLabel.className = 'tc-role-nav-label';
    settingsLabel.textContent = 'Settings';

    settingsButton.append(settingsIcon, settingsLabel);

    settingsButton.addEventListener('click', function (event) {
    event.preventDefault();
    event.stopPropagation();

    const isOpen = !popup.classList.contains('tc-open');

    popup.classList.toggle('tc-open', isOpen);

    settingsButton.setAttribute(
        'aria-expanded',
        String(isOpen)
    );
});

    // Close the popup when another area is tapped.
   document.addEventListener('click', function (event) {
    if (
        !popup.contains(event.target) &&
        !settingsButton.contains(event.target)
    ) {
        popup.classList.remove('tc-open');
        settingsButton.setAttribute('aria-expanded', 'false');
    }
});

    // Close the popup when a navigation link is selected.
    popup.addEventListener('click', function (event) {
        if (event.target.closest('a')) {
            popup.classList.remove('tc-open');
            settingsButton.setAttribute('aria-expanded', 'false');
        }
    });

    bottomItems.appendChild(settingsButton);
    navigation.append(popup, bottomItems);

    // Display the new navigation.
    root.classList.add('tc-has-role-nav');
    navigation.style.display = 'block';

})();
