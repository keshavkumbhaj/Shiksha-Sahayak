/**
 * Student Module JavaScript
 * Handles Student Dashboard and Interactive Learning Setup
 */

// Mock Academic Knowledge Base (Courses, Units, Topics)
const COURSE_SYLLABUS = {
    dbms: {
        id: "dbms",
        name: "Database Management Systems (CS-301)",
        shortName: "DBMS",
        icon: "🗄️",
        colorClass: "dbms",
        teacher: "Prof. Sharma",
        units: [
            {
                id: "u1",
                name: "Unit 1: Introduction to DBMS",
                topics: [
                    { id: "t_arch", name: "Database Architecture & 3-Tier Schema" },
                    { id: "t_indep", name: "Physical & Logical Data Independence" },
                    { id: "t_er", name: "ER Modeling & Key Constraints" }
                ]
            },
            {
                id: "u2",
                name: "Unit 2: Relational Model & SQL",
                topics: [
                    { id: "t_relalg", name: "Relational Algebra Operations" },
                    { id: "t_sql", name: "DDL, DML, and Aggregate SQL Queries" },
                    { id: "t_joins", name: "SQL Joins & Integrity Constraints" }
                ]
            },
            {
                id: "u3",
                name: "Unit 3: Normalization & Functional Dependencies",
                topics: [
                    { id: "t_fd", name: "Functional Dependencies & Attribute Closure" },
                    { id: "t_1nf2nf", name: "First & Second Normal Form (1NF & 2NF)" },
                    { id: "t_norm", name: "Normalization (3NF & BCNF)" },
                    { id: "t_mvd", name: "Multivalued Dependencies & 4NF" }
                ]
            },
            {
                id: "u4",
                name: "Unit 4: Transaction Processing & Concurrency",
                topics: [
                    { id: "t_acid", name: "Transaction States & ACID Properties" },
                    { id: "t_ser", name: "Conflict & View Serializability" },
                    { id: "t_lock", name: "Two-Phase Locking (2PL) Protocol" }
                ]
            }
        ]
    },
    os: {
        id: "os",
        name: "Operating Systems (CS-302)",
        shortName: "OS",
        icon: "💻",
        colorClass: "os",
        teacher: "Dr. K. Rao",
        units: [
            {
                id: "os_u1",
                name: "Unit 1: OS Structures & System Calls",
                topics: [
                    { id: "os_t1", name: "Dual-Mode Operations & System Calls" },
                    { id: "os_t2", name: "Kernel Architectures (Monolithic vs Micro)" }
                ]
            },
            {
                id: "os_u2",
                name: "Unit 2: Process Synchronization & Deadlocks",
                topics: [
                    { id: "os_t3", name: "Critical Section & Peterson's Algorithm" },
                    { id: "os_t4", name: "Banker's Algorithm for Deadlock Avoidance" }
                ]
            }
        ]
    },
    cn: {
        id: "cn",
        name: "Computer Networks (CS-303)",
        shortName: "CN",
        icon: "🌐",
        colorClass: "cn",
        teacher: "Prof. Ananya Gupta",
        units: [
            {
                id: "cn_u1",
                name: "Unit 1: Physical & Data Link Layer",
                topics: [
                    { id: "cn_t1", name: "OSI Reference Model vs TCP/IP" },
                    { id: "cn_t2", name: "Sliding Window Protocols (Go-Back-N, SR)" }
                ]
            },
            {
                id: "cn_u2",
                name: "Unit 2: Network Layer & Routing",
                topics: [
                    { id: "cn_t3", name: "IPv4 Subnetting & CIDR" },
                    { id: "cn_t4", name: "Distance Vector vs Link State Routing" }
                ]
            }
        ]
    }
};

// Current Learning Setup Configuration State
const learningConfig = {
    courseId: "",
    unitId: "",
    topicId: "",
    level: "intermediate", // 'basic' | 'intermediate' | 'advanced'
    language: "english",   // 'english' | 'hindi'
    marks: "5",            // '2' | '5' | '10'
    mode: "exam_answer"    // 'learn_simply' | 'exam_answer'
};

/* =========================================================
   Learning Setup Controller (learning.html)
   ========================================================= */

function initLearningSetup() {
    populateCourseDropdown();
    attachPillSelectorEvents();

    // Check URL search parameters or demo defaults
    const urlParams = new URLSearchParams(window.location.search);
    const courseParam = urlParams.get('course');
    const unitParam = urlParams.get('unit');
    const topicParam = urlParams.get('topic');
    const levelParam = urlParams.get('level');
    const langParam = urlParams.get('lang');
    const marksParam = urlParams.get('marks');
    const modeParam = urlParams.get('mode');

    if (courseParam && COURSE_SYLLABUS[courseParam]) {
        learningConfig.courseId = courseParam;
        if (unitParam) learningConfig.unitId = unitParam;
        if (topicParam) learningConfig.topicId = topicParam;
        if (levelParam) learningConfig.level = levelParam;
        if (langParam) learningConfig.language = langParam;
        if (marksParam) learningConfig.marks = marksParam;
        if (modeParam) learningConfig.mode = modeParam;
        syncStateToUI();
    } else {
        // Check saved session or start with empty course selection
        const saved = localStorage.getItem('shiksha_student_setup');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                Object.assign(learningConfig, parsed);
                syncStateToUI();
            } catch (e) {
                // Ignore parse errors and fallback
            }
        }
    }

    updateSummaryAndReadiness();
}

/**
 * Populates the course select dropdown
 */
function populateCourseDropdown() {
    const courseSelect = document.getElementById('student-course-select');
    if (!courseSelect) return;

    courseSelect.innerHTML = '<option value="">-- Choose a Course --</option>';
    Object.keys(COURSE_SYLLABUS).forEach(key => {
        const course = COURSE_SYLLABUS[key];
        const opt = document.createElement('option');
        opt.value = course.id;
        opt.textContent = `${course.name} (${course.teacher})`;
        courseSelect.appendChild(opt);
    });

    courseSelect.addEventListener('change', (e) => {
        onCourseChange(e.target.value);
    });
}

/**
 * Handle Course selection change
 */
function onCourseChange(courseId) {
    learningConfig.courseId = courseId;
    learningConfig.unitId = "";
    learningConfig.topicId = "";

    const unitSelect = document.getElementById('student-unit-select');
    const topicSelect = document.getElementById('student-topic-select');

    if (!unitSelect || !topicSelect) return;

    topicSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
    topicSelect.disabled = true;

    if (!courseId || !COURSE_SYLLABUS[courseId]) {
        unitSelect.innerHTML = '<option value="">-- Select Course First --</option>';
        unitSelect.disabled = true;
        updateSummaryAndReadiness();
        return;
    }

    unitSelect.disabled = false;
    unitSelect.innerHTML = '<option value="">-- Choose a Unit --</option>';
    
    COURSE_SYLLABUS[courseId].units.forEach(unit => {
        const opt = document.createElement('option');
        opt.value = unit.id;
        opt.textContent = unit.name;
        unitSelect.appendChild(opt);
    });

    unitSelect.onchange = (e) => onUnitChange(e.target.value);
    updateSummaryAndReadiness();
}

/**
 * Handle Unit selection change
 */
function onUnitChange(unitId) {
    learningConfig.unitId = unitId;
    learningConfig.topicId = "";

    const topicSelect = document.getElementById('student-topic-select');
    if (!topicSelect) return;

    if (!unitId) {
        topicSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
        topicSelect.disabled = true;
        updateSummaryAndReadiness();
        return;
    }

    const course = COURSE_SYLLABUS[learningConfig.courseId];
    if (!course) return;

    const unit = course.units.find(u => u.id === unitId);
    if (!unit) return;

    topicSelect.disabled = false;
    topicSelect.innerHTML = '<option value="">-- Choose a Topic --</option>';

    unit.topics.forEach(topic => {
        const opt = document.createElement('option');
        opt.value = topic.id;
        opt.textContent = topic.name;
        topicSelect.appendChild(opt);
    });

    topicSelect.onchange = (e) => onTopicChange(e.target.value);
    updateSummaryAndReadiness();
}

/**
 * Handle Topic selection change
 */
function onTopicChange(topicId) {
    learningConfig.topicId = topicId;
    updateSummaryAndReadiness();
    saveSetupState();
}

/**
 * Attach click listeners to pill options (Level, Language, Marks, Mode)
 */
function attachPillSelectorEvents() {
    // Level selection
    document.querySelectorAll('[data-level]').forEach(el => {
        el.addEventListener('click', () => {
            document.querySelectorAll('[data-level]').forEach(p => p.classList.remove('selected'));
            el.classList.add('selected');
            learningConfig.level = el.getAttribute('data-level');
            updateSummaryAndReadiness();
            saveSetupState();
        });
    });

    // Language selection
    document.querySelectorAll('[data-lang]').forEach(el => {
        el.addEventListener('click', () => {
            document.querySelectorAll('[data-lang]').forEach(p => p.classList.remove('selected'));
            el.classList.add('selected');
            learningConfig.language = el.getAttribute('data-lang');
            updateSummaryAndReadiness();
            saveSetupState();
        });
    });

    // Marks selection
    document.querySelectorAll('[data-marks]').forEach(el => {
        el.addEventListener('click', () => {
            document.querySelectorAll('[data-marks]').forEach(p => p.classList.remove('selected'));
            el.classList.add('selected');
            learningConfig.marks = el.getAttribute('data-marks');
            updateSummaryAndReadiness();
            saveSetupState();
        });
    });

    // Mode selection (Learn Simply vs Exam Answer)
    document.querySelectorAll('[data-mode]').forEach(el => {
        el.addEventListener('click', () => {
            document.querySelectorAll('[data-mode]').forEach(m => m.classList.remove('selected'));
            el.classList.add('selected');
            learningConfig.mode = el.getAttribute('data-mode');
            updateSummaryAndReadiness();
            saveSetupState();
        });
    });
}

/**
 * Preloads the primary demo flow required by SIH & Keshav:
 * DBMS → Unit 3 → Normalization → Intermediate → English → 5 Marks → Exam Answer
 */
function loadDemoFlow() {
    learningConfig.courseId = "dbms";
    learningConfig.unitId = "u3";
    learningConfig.topicId = "t_norm";
    learningConfig.level = "intermediate";
    learningConfig.language = "english";
    learningConfig.marks = "5";
    learningConfig.mode = "exam_answer";

    syncStateToUI();
    saveSetupState();

    if (typeof showToast === 'function') {
        showToast("Primary Demo Flow Loaded: DBMS > Unit 3 > Normalization (5 Marks, Exam Answer)", "success");
    }
}

/**
 * Synchronizes JavaScript state into the HTML select elements and active CSS classes
 */
function syncStateToUI() {
    const courseSelect = document.getElementById('student-course-select');
    if (courseSelect) {
        courseSelect.value = learningConfig.courseId;
        onCourseChange(learningConfig.courseId);
    }

    const unitSelect = document.getElementById('student-unit-select');
    if (unitSelect && learningConfig.unitId) {
        unitSelect.value = learningConfig.unitId;
        onUnitChange(learningConfig.unitId);
    }

    const topicSelect = document.getElementById('student-topic-select');
    if (topicSelect && learningConfig.topicId) {
        topicSelect.value = learningConfig.topicId;
    }

    // Sync Level
    document.querySelectorAll('[data-level]').forEach(el => {
        el.classList.toggle('selected', el.getAttribute('data-level') === learningConfig.level);
    });

    // Sync Language
    document.querySelectorAll('[data-lang]').forEach(el => {
        el.classList.toggle('selected', el.getAttribute('data-lang') === learningConfig.language);
    });

    // Sync Marks
    document.querySelectorAll('[data-marks]').forEach(el => {
        el.classList.toggle('selected', el.getAttribute('data-marks') === learningConfig.marks);
    });

    // Sync Mode
    document.querySelectorAll('[data-mode]').forEach(el => {
        el.classList.toggle('selected', el.getAttribute('data-mode') === learningConfig.mode);
    });

    updateSummaryAndReadiness();
}

/**
 * Updates summary chips, displays validation state, and readiness to generate
 */
function updateSummaryAndReadiness() {
    const summaryCard = document.getElementById('summary-card');
    const summaryChips = document.getElementById('summary-chips');
    const readyBox = document.getElementById('ready-box');
    const generateBtn = document.getElementById('btn-generate-prep');
    const incompleteAlert = document.getElementById('incomplete-alert');

    if (!summaryCard) return;

    const hasCourse = Boolean(learningConfig.courseId && COURSE_SYLLABUS[learningConfig.courseId]);
    const courseObj = hasCourse ? COURSE_SYLLABUS[learningConfig.courseId] : null;
    const unitObj = hasCourse && learningConfig.unitId ? courseObj.units.find(u => u.id === learningConfig.unitId) : null;
    const topicObj = unitObj && learningConfig.topicId ? unitObj.topics.find(t => t.id === learningConfig.topicId) : null;

    const isComplete = Boolean(hasCourse && unitObj && topicObj && learningConfig.level && learningConfig.language && learningConfig.marks && learningConfig.mode);

    if (summaryChips) {
        summaryChips.innerHTML = `
            <span class="summary-chip"><strong>Course:</strong> ${courseObj ? courseObj.shortName : "—"}</span>
            <span class="summary-chip"><strong>Unit:</strong> ${unitObj ? unitObj.name.split(':')[0] : "—"}</span>
            <span class="summary-chip"><strong>Topic:</strong> ${topicObj ? topicObj.name : "Not selected"}</span>
            <span class="summary-chip"><strong>Level:</strong> ${capitalize(learningConfig.level)}</span>
            <span class="summary-chip"><strong>Language:</strong> ${learningConfig.language === 'english' ? 'English (EN)' : 'Hindi (हिन्दी)'}</span>
            <span class="summary-chip"><strong>Marks:</strong> ${learningConfig.marks} Marks</span>
            <span class="summary-chip"><strong>Mode:</strong> ${learningConfig.mode === 'exam_answer' ? 'Exam Answer' : 'Learn Simply'}</span>
        `;
    }

    if (isComplete) {
        if (readyBox) readyBox.style.display = 'flex';
        if (incompleteAlert) incompleteAlert.style.display = 'none';
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.classList.remove('btn-secondary');
            generateBtn.classList.add('btn-primary');
        }
    } else {
        if (readyBox) readyBox.style.display = 'none';
        if (incompleteAlert) {
            incompleteAlert.style.display = 'block';
            if (!hasCourse) {
                incompleteAlert.innerText = "Please select a Course to begin.";
            } else if (!unitObj) {
                incompleteAlert.innerText = "Please select a Unit from the syllabus.";
            } else if (!topicObj) {
                incompleteAlert.innerText = "Please select a Topic to complete setup.";
            }
        }
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.classList.remove('btn-primary');
            generateBtn.classList.add('btn-secondary');
        }
    }
}

/**
 * Handles the "Ready to Generate Answer" CTA
 * Simulates content readiness check and shows generation pipeline preview
 */
function prepareGeneration() {
    const hasCourse = Boolean(learningConfig.courseId && COURSE_SYLLABUS[learningConfig.courseId]);
    const courseObj = hasCourse ? COURSE_SYLLABUS[learningConfig.courseId] : null;
    const unitObj = hasCourse && learningConfig.unitId ? courseObj.units.find(u => u.id === learningConfig.unitId) : null;
    const topicObj = unitObj && learningConfig.topicId ? unitObj.topics.find(t => t.id === learningConfig.topicId) : null;

    if (!topicObj) {
        if (typeof showToast === 'function') {
            showToast("Please complete the setup: Course, Unit, and Topic are required.", "error");
        }
        return;
    }

    const loadingBox = document.getElementById('generation-loading');
    const pipelinePreview = document.getElementById('generation-pipeline-preview');
    const setupCard = document.getElementById('setup-main-card');

    if (loadingBox) {
        loadingBox.classList.add('active');
        if (pipelinePreview) pipelinePreview.style.display = 'none';

        // Smooth scroll to loading section
        loadingBox.scrollIntoView({ behavior: 'smooth', block: 'center' });

        setTimeout(() => {
            loadingBox.classList.remove('active');
            if (pipelinePreview) {
                pipelinePreview.style.display = 'block';
                pipelinePreview.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            if (typeof showToast === 'function') {
                showToast(`Setup validated for ${topicObj.name}! Ready for AI Generation.`, "success");
            }
        }, 1200);
    }
}

/**
 * Saves current setup to browser storage
 */
function saveSetupState() {
    try {
        localStorage.setItem('shiksha_student_setup', JSON.stringify(learningConfig));
    } catch (e) {
        // Storage not available or private mode
    }
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/* =========================================================
   Student Dashboard Logic (dashboard.html)
   ========================================================= */

function initStudentDashboard() {
    // Populate or wire dashboard elements
    const demoBtn = document.getElementById('btn-dashboard-demo');
    if (demoBtn) {
        demoBtn.addEventListener('click', () => {
            window.location.href = "learning.html?course=dbms&unit=u3&topic=t_norm&level=intermediate&lang=english&marks=5&mode=exam_answer";
        });
    }
}

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('student-course-select')) {
        initLearningSetup();
    }
    if (document.getElementById('student-dashboard-root')) {
        initStudentDashboard();
    }
});
