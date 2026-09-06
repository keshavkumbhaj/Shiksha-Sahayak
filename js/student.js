/**
 * Student Module JavaScript
 * Handles Dynamic Student Course -> Unit -> Topic Selection from Backend
 * and Verified Student Adaptation Preference State
 */

const STUDENT_API_BASE = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : '/api';

// Allowed backend contract values
const VALID_LEVELS = ["basic", "intermediate", "advanced"];
const VALID_LANGUAGES = ["english", "hindi"];
const VALID_MARKS = [2, 5, 10];
const VALID_MODES = ["exam", "exam_answer", "learn", "learn_simply"];

// State for dynamically loaded syllabus data from backend
let availableCourses = [];         // Array from GET /api/courses
let currentCourseHierarchy = null; // Object from GET /api/courses/<id>

// Current Learning Setup Configuration State (using real numeric IDs and validated types)
const learningConfig = {
    courseId: null,        // numeric course_id (integer)
    unitId: null,          // numeric unit_id (integer)
    topicId: null,         // numeric topic_id (integer)
    level: "intermediate", // 'basic' | 'intermediate' | 'advanced'
    language: "english",   // 'english' | 'hindi'
    marks: 5,              // 2 | 5 | 10 (integer)
    mode: "exam_answer"    // 'learn_simply' | 'exam_answer'
};

/* =========================================================
   Learning Setup Controller (learning.html)
   ========================================================= */

async function initLearningSetup() {
    attachPillSelectorEvents();

    // 1. Fetch courses from GET /api/courses
    await loadStudentCourses();

    // 2. Check URL search parameters
    const urlParams = new URLSearchParams(window.location.search);
    const courseParam = urlParams.get('course_id') || urlParams.get('course');
    const unitParam = urlParams.get('unit_id') || urlParams.get('unit');
    const topicParam = urlParams.get('topic_id') || urlParams.get('topic');
    const levelParam = urlParams.get('level');
    const langParam = urlParams.get('lang');
    const marksParam = urlParams.get('marks');
    const modeParam = urlParams.get('mode');

    if (levelParam && VALID_LEVELS.includes(levelParam.toLowerCase())) {
        learningConfig.level = levelParam.toLowerCase();
    }
    if (langParam && VALID_LANGUAGES.includes(langParam.toLowerCase())) {
        learningConfig.language = langParam.toLowerCase();
    }
    if (marksParam) {
        const parsedMarks = parseInt(marksParam, 10);
        if (VALID_MARKS.includes(parsedMarks)) {
            learningConfig.marks = parsedMarks;
        }
    }
    if (modeParam && VALID_MODES.includes(modeParam.toLowerCase())) {
        learningConfig.mode = modeParam.toLowerCase();
    }
    syncPillsToUI();

    if (courseParam) {
        let matchedCourseId = parseInt(courseParam, 10);
        if (isNaN(matchedCourseId) && availableCourses.length > 0) {
            const found = availableCourses.find(c => c.course_name.toLowerCase().includes(courseParam.toLowerCase()));
            matchedCourseId = found ? found.course_id : availableCourses[0].course_id;
        }

        if (!isNaN(matchedCourseId)) {
            const courseSelect = document.getElementById('student-course-select');
            if (courseSelect) {
                courseSelect.value = String(matchedCourseId);
            }
            await onCourseChange(matchedCourseId);

            let matchedUnitId = parseInt(unitParam, 10);
            if (isNaN(matchedUnitId) && currentCourseHierarchy && currentCourseHierarchy.units && currentCourseHierarchy.units.length > 0) {
                if (topicParam) {
                    const tVal = parseInt(topicParam, 10);
                    const parentUnit = currentCourseHierarchy.units.find(u => u.topics && u.topics.some(t => t.topic_id === tVal || (isNaN(tVal) && t.topic_name.toLowerCase().includes(topicParam.toLowerCase()))));
                    if (parentUnit) matchedUnitId = parentUnit.unit_id;
                }
                if (isNaN(matchedUnitId)) {
                    if (unitParam === 'u3' || unitParam === '3') {
                        const u = currentCourseHierarchy.units.find(u => u.unit_number === 3 || u.unit_id === 1);
                        if (u) matchedUnitId = u.unit_id;
                    } else {
                        matchedUnitId = currentCourseHierarchy.units[0].unit_id;
                    }
                }
            }

            if (!isNaN(matchedUnitId) && currentCourseHierarchy) {
                const unitSelect = document.getElementById('student-unit-select');
                if (unitSelect) {
                    unitSelect.value = String(matchedUnitId);
                }
                onUnitChange(matchedUnitId);

                let matchedTopicId = parseInt(topicParam, 10);
                if (isNaN(matchedTopicId) && currentCourseHierarchy && currentCourseHierarchy.units) {
                    const unitObj = currentCourseHierarchy.units.find(u => u.unit_id === matchedUnitId);
                    if (unitObj && unitObj.topics && unitObj.topics.length > 0) {
                        if (topicParam === 't_norm') {
                            const t = unitObj.topics.find(t => t.topic_name.toLowerCase().includes('normalization'));
                            matchedTopicId = t ? t.topic_id : unitObj.topics[0].topic_id;
                        } else {
                            matchedTopicId = unitObj.topics[0].topic_id;
                        }
                    }
                }

                if (!isNaN(matchedTopicId)) {
                    const topicSelect = document.getElementById('student-topic-select');
                    if (topicSelect) {
                        topicSelect.value = String(matchedTopicId);
                    }
                    onTopicChange(matchedTopicId);
                }
            }
        }
    } else {
        updateSummaryAndReadiness();
    }
}

/**
 * Loads courses from backend GET /api/courses and populates dropdown
 */
async function loadStudentCourses() {
    const courseSelect = document.getElementById('student-course-select');
    if (!courseSelect) return;

    courseSelect.innerHTML = '<option value="">Loading courses from database...</option>';

    try {
        const res = await fetch(`${STUDENT_API_BASE}/courses`);
        if (!res.ok) {
            throw new Error(`Server returned status ${res.status}`);
        }
        const data = await res.json();
        availableCourses = Array.isArray(data) ? data : (data.courses || []);

        courseSelect.innerHTML = '<option value="">-- Choose a Course --</option>';
        if (availableCourses.length === 0) {
            courseSelect.innerHTML = '<option value="">No courses available</option>';
            return;
        }

        availableCourses.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.course_id; // Store real numeric ID
            opt.textContent = `${c.course_name} (ID: ${c.course_id})`;
            courseSelect.appendChild(opt);
        });

        courseSelect.addEventListener('change', async (e) => {
            const val = e.target.value;
            await onCourseChange(val ? parseInt(val, 10) : null);
        });

    } catch (err) {
        console.error('Failed to load courses for student:', err);
        courseSelect.innerHTML = '<option value="">Failed to load courses</option>';
        if (typeof showToast === 'function') {
            showToast('Unable to connect to courses backend API.', 'error');
        }
    }
}

/**
 * Handles Course selection change and retrieves hierarchy via GET /api/courses/<id>
 */
async function onCourseChange(courseId) {
    learningConfig.courseId = courseId ? parseInt(courseId, 10) : null;
    learningConfig.unitId = null;
    learningConfig.topicId = null;
    currentCourseHierarchy = null;

    const unitSelect = document.getElementById('student-unit-select');
    const topicSelect = document.getElementById('student-topic-select');

    if (!unitSelect || !topicSelect) return;

    topicSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
    topicSelect.disabled = true;

    if (!courseId) {
        unitSelect.innerHTML = '<option value="">-- Select Course First --</option>';
        unitSelect.disabled = true;
        updateSummaryAndReadiness();
        return;
    }

    unitSelect.disabled = true;
    unitSelect.innerHTML = '<option value="">Loading units...</option>';

    try {
        const res = await fetch(`${STUDENT_API_BASE}/courses/${courseId}`);
        if (!res.ok) {
            throw new Error(`Failed to load course details (${res.status})`);
        }
        currentCourseHierarchy = await res.json();

        const units = currentCourseHierarchy.units || [];
        if (units.length === 0) {
            unitSelect.innerHTML = '<option value="">No units available for this course</option>';
            unitSelect.disabled = true;
            updateSummaryAndReadiness();
            return;
        }

        unitSelect.innerHTML = '<option value="">-- Choose a Unit --</option>';
        units.forEach(unit => {
            const opt = document.createElement('option');
            opt.value = unit.unit_id; // Store real numeric ID
            opt.textContent = unit.unit_name || `Unit ${unit.unit_number}`;
            unitSelect.appendChild(opt);
        });
        unitSelect.disabled = false;

        unitSelect.onchange = (e) => {
            const uVal = e.target.value;
            onUnitChange(uVal ? parseInt(uVal, 10) : null);
        };

    } catch (err) {
        console.error('Error fetching course hierarchy:', err);
        unitSelect.innerHTML = '<option value="">Error loading units</option>';
        unitSelect.disabled = true;
        if (typeof showToast === 'function') {
            showToast('Error loading course syllabus units.', 'error');
        }
    }

    updateSummaryAndReadiness();
}

/**
 * Handles Unit selection change and populates topics dynamically
 */
function onUnitChange(unitId) {
    learningConfig.unitId = unitId ? parseInt(unitId, 10) : null;
    learningConfig.topicId = null;

    const topicSelect = document.getElementById('student-topic-select');
    if (!topicSelect) return;

    if (!unitId || !currentCourseHierarchy) {
        topicSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
        topicSelect.disabled = true;
        updateSummaryAndReadiness();
        return;
    }

    const units = currentCourseHierarchy.units || [];
    const unit = units.find(u => u.unit_id === learningConfig.unitId);
    if (!unit || !unit.topics || unit.topics.length === 0) {
        topicSelect.innerHTML = '<option value="">No topics in this unit</option>';
        topicSelect.disabled = true;
        updateSummaryAndReadiness();
        return;
    }

    topicSelect.disabled = false;
    topicSelect.innerHTML = '<option value="">-- Choose a Topic --</option>';

    unit.topics.forEach(topic => {
        const opt = document.createElement('option');
        opt.value = topic.topic_id; // Store real numeric ID
        opt.textContent = topic.topic_name;
        topicSelect.appendChild(opt);
    });

    topicSelect.onchange = (e) => {
        const tVal = e.target.value;
        onTopicChange(tVal ? parseInt(tVal, 10) : null);
    };

    updateSummaryAndReadiness();
}

/**
 * Handles Topic selection change
 */
function onTopicChange(topicId) {
    learningConfig.topicId = topicId ? parseInt(topicId, 10) : null;
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
            const val = el.getAttribute('data-level');
            if (VALID_LEVELS.includes(val)) {
                document.querySelectorAll('[data-level]').forEach(p => p.classList.remove('selected'));
                el.classList.add('selected');
                learningConfig.level = val;
                updateSummaryAndReadiness();
                saveSetupState();
            }
        });
    });

    // Language selection
    document.querySelectorAll('[data-lang]').forEach(el => {
        el.addEventListener('click', () => {
            const val = el.getAttribute('data-lang');
            if (VALID_LANGUAGES.includes(val)) {
                document.querySelectorAll('[data-lang]').forEach(p => p.classList.remove('selected'));
                el.classList.add('selected');
                learningConfig.language = val;
                updateSummaryAndReadiness();
                saveSetupState();
            }
        });
    });

    // Marks selection (ensures integer storage)
    document.querySelectorAll('[data-marks]').forEach(el => {
        el.addEventListener('click', () => {
            const val = parseInt(el.getAttribute('data-marks'), 10);
            if (VALID_MARKS.includes(val)) {
                document.querySelectorAll('[data-marks]').forEach(p => p.classList.remove('selected'));
                el.classList.add('selected');
                learningConfig.marks = val;
                updateSummaryAndReadiness();
                saveSetupState();
            }
        });
    });

    // Mode selection (Learn Simply vs Exam Answer)
    document.querySelectorAll('[data-mode]').forEach(el => {
        el.addEventListener('click', () => {
            const val = el.getAttribute('data-mode');
            if (VALID_MODES.includes(val)) {
                document.querySelectorAll('[data-mode]').forEach(m => m.classList.remove('selected'));
                el.classList.add('selected');
                learningConfig.mode = val;
                updateSummaryAndReadiness();
                saveSetupState();
            }
        });
    });
}

/**
 * Preloads the primary demo flow using real backend data:
 * DBMS (course_id: 1) -> Unit 3 (unit_id: 1) -> Normalization (topic_id: 1)
 */
async function loadDemoFlow() {
    if (!availableCourses || availableCourses.length === 0) {
        await loadStudentCourses();
    }

    const courseSelect = document.getElementById('student-course-select');
    if (!courseSelect) return;

    // Locate DBMS course (ID 1)
    const dbmsCourse = availableCourses.find(c => c.course_id === 1 || c.course_name.toUpperCase().includes('DBMS')) || availableCourses[0];
    if (!dbmsCourse) {
        if (typeof showToast === 'function') {
            showToast('No courses available in database.', 'warning');
        }
        return;
    }

    courseSelect.value = String(dbmsCourse.course_id);
    await onCourseChange(dbmsCourse.course_id);

    const unitSelect = document.getElementById('student-unit-select');
    if (unitSelect && currentCourseHierarchy && currentCourseHierarchy.units && currentCourseHierarchy.units.length > 0) {
        const unit = currentCourseHierarchy.units.find(u => u.unit_id === 1 || u.unit_number === 3) || currentCourseHierarchy.units[0];
        unitSelect.value = String(unit.unit_id);
        onUnitChange(unit.unit_id);

        const topicSelect = document.getElementById('student-topic-select');
        if (topicSelect && unit.topics && unit.topics.length > 0) {
            const topic = unit.topics.find(t => t.topic_id === 1 || t.topic_name.toLowerCase().includes('normalization')) || unit.topics[0];
            topicSelect.value = String(topic.topic_id);
            onTopicChange(topic.topic_id);
        }
    }

    learningConfig.level = "intermediate";
    learningConfig.language = "english";
    learningConfig.marks = 5;
    learningConfig.mode = "exam_answer";

    syncPillsToUI();
    saveSetupState();

    if (typeof showToast === 'function') {
        showToast("Primary Demo Flow Loaded: DBMS > Unit 3 > Normalization (5 Marks, Exam Answer)", "success");
    }
}

/**
 * Synchronizes Level, Language, Marks, and Mode pill states to DOM
 */
function syncPillsToUI() {
    document.querySelectorAll('[data-level]').forEach(el => {
        el.classList.toggle('selected', el.getAttribute('data-level') === learningConfig.level);
    });

    document.querySelectorAll('[data-lang]').forEach(el => {
        el.classList.toggle('selected', el.getAttribute('data-lang') === learningConfig.language);
    });

    document.querySelectorAll('[data-marks]').forEach(el => {
        el.classList.toggle('selected', parseInt(el.getAttribute('data-marks'), 10) === learningConfig.marks);
    });

    document.querySelectorAll('[data-mode]').forEach(el => {
        el.classList.toggle('selected', el.getAttribute('data-mode') === learningConfig.mode);
    });

    updateSummaryAndReadiness();
}

/**
 * Validates that all 7 required parameters are selected and conform to backend contracts
 */
function isConfigurationValid() {
    const hasCourse = Number.isInteger(learningConfig.courseId) && learningConfig.courseId > 0;
    const hasUnit = Number.isInteger(learningConfig.unitId) && learningConfig.unitId > 0;
    const hasTopic = Number.isInteger(learningConfig.topicId) && learningConfig.topicId > 0;
    const hasLevel = Boolean(learningConfig.level && VALID_LEVELS.includes(learningConfig.level));
    const hasLanguage = Boolean(learningConfig.language && VALID_LANGUAGES.includes(learningConfig.language));
    const hasMarks = Boolean(learningConfig.marks && VALID_MARKS.includes(learningConfig.marks));
    const hasMode = Boolean(learningConfig.mode && VALID_MODES.includes(learningConfig.mode));

    return Boolean(hasCourse && hasUnit && hasTopic && hasLevel && hasLanguage && hasMarks && hasMode);
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

    let courseName = "—";
    let unitName = "—";
    let topicName = "Not selected";

    if (availableCourses.length > 0 && learningConfig.courseId !== null) {
        const c = availableCourses.find(c => c.course_id === learningConfig.courseId);
        if (c) courseName = c.course_name;
    }
    if (currentCourseHierarchy && currentCourseHierarchy.units && learningConfig.unitId !== null) {
        const u = currentCourseHierarchy.units.find(u => u.unit_id === learningConfig.unitId);
        if (u) unitName = u.unit_name ? u.unit_name.split(':')[0] : `Unit ${u.unit_number}`;
    }
    if (currentCourseHierarchy && currentCourseHierarchy.units && learningConfig.unitId !== null && learningConfig.topicId !== null) {
        const u = currentCourseHierarchy.units.find(u => u.unit_id === learningConfig.unitId);
        if (u && u.topics) {
            const t = u.topics.find(t => t.topic_id === learningConfig.topicId);
            if (t) topicName = t.topic_name;
        }
    }

    const hasCourse = Number.isInteger(learningConfig.courseId) && learningConfig.courseId > 0;
    const hasUnit = Number.isInteger(learningConfig.unitId) && learningConfig.unitId > 0;
    const hasTopic = Number.isInteger(learningConfig.topicId) && learningConfig.topicId > 0;
    const hasLevel = Boolean(learningConfig.level && VALID_LEVELS.includes(learningConfig.level));
    const hasLanguage = Boolean(learningConfig.language && VALID_LANGUAGES.includes(learningConfig.language));
    const hasMarks = Boolean(learningConfig.marks && VALID_MARKS.includes(learningConfig.marks));
    const hasMode = Boolean(learningConfig.mode && VALID_MODES.includes(learningConfig.mode));

    const isComplete = Boolean(hasCourse && hasUnit && hasTopic && hasLevel && hasLanguage && hasMarks && hasMode);

    if (summaryChips) {
        const escape = (typeof escapeHTML === 'function') ? escapeHTML : (s => s);
        summaryChips.innerHTML = `
            <span class="summary-chip"><strong>Course:</strong> ${escape(courseName)}</span>
            <span class="summary-chip"><strong>Unit:</strong> ${escape(unitName)}</span>
            <span class="summary-chip"><strong>Topic:</strong> ${escape(topicName)}</span>
            <span class="summary-chip"><strong>Level:</strong> ${hasLevel ? capitalize(learningConfig.level) : "Not selected"}</span>
            <span class="summary-chip"><strong>Language:</strong> ${hasLanguage ? (learningConfig.language === 'english' ? 'English (EN)' : 'Hindi (हिन्दी)') : "Not selected"}</span>
            <span class="summary-chip"><strong>Marks:</strong> ${hasMarks ? `${learningConfig.marks} Marks` : "Not selected"}</span>
            <span class="summary-chip"><strong>Mode:</strong> ${hasMode ? (learningConfig.mode === 'exam_answer' ? 'Exam Answer' : 'Learn Simply') : "Not selected"}</span>
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
            } else if (!hasUnit) {
                incompleteAlert.innerText = "Please select a Unit from the syllabus.";
            } else if (!hasTopic) {
                incompleteAlert.innerText = "Please select a Topic to complete setup.";
            } else if (!hasLevel) {
                incompleteAlert.innerText = "Please select a Learning Level (Basic, Intermediate, or Advanced).";
            } else if (!hasLanguage) {
                incompleteAlert.innerText = "Please select a Preferred Language (English or Hindi).";
            } else if (!hasMarks) {
                incompleteAlert.innerText = "Please select Target Marks (2, 5, or 10 Marks).";
            } else if (!hasMode) {
                incompleteAlert.innerText = "Please select a Learning Mode (Learn Simply or Exam Answer).";
            }
        }
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.classList.remove('btn-primary');
            generateBtn.classList.add('btn-secondary');
        }
    }

    const mcqBtn = document.getElementById('btn-topic-assessment');
    if (mcqBtn) {
        mcqBtn.disabled = !hasTopic;
    }
}

/**
 * Connects to POST /api/answers/generate to request grounded answer
 * Implements 5 legitimate UI states:
 * 1. Ready to generate
 * 2. Generating
 * 3. Successfully generated (if real AI generated)
 * 4. Generation unavailable/pending (if awaiting ai.generator)
 * 5. API error
 */
async function generateAnswer() {
    if (!isConfigurationValid()) {
        if (typeof showToast === 'function') {
            showToast("Please select all required learning parameters (Course, Unit, Topic, Level, Language, Marks, and Mode).", "error");
        }
        return;
    }

    const generateBtn = document.getElementById('btn-generate-prep');
    const loadingBox = document.getElementById('generation-loading');
    const resultContainer = document.getElementById('generation-result-container');
    const errorBox = document.getElementById('generation-error-box');
    const errorMessage = document.getElementById('generation-error-message');

    // UI State: Generating
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerText = "Generating Grounded Answer...";
    }
    if (errorBox) errorBox.style.display = 'none';
    if (resultContainer) resultContainer.style.display = 'none';
    if (loadingBox) {
        loadingBox.classList.add('active');
        loadingBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Exact required payload (marks as integer, course_id, topic_id, level, language, mode)
    const payload = {
        course_id: parseInt(learningConfig.courseId, 10),
        topic_id: parseInt(learningConfig.topicId, 10),
        level: String(learningConfig.level),
        language: String(learningConfig.language),
        marks: parseInt(learningConfig.marks, 10),
        mode: String(learningConfig.mode)
    };

    try {
        const res = await fetch(`${STUDENT_API_BASE}/answers/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (loadingBox) loadingBox.classList.remove('active');

        if (!res.ok) {
            // UI State: API error
            const errDetail = (data && data.error) ? data.error : `HTTP ${res.status}: Failed to generate answer`;
            if (errorBox) {
                if (errorMessage) errorMessage.innerText = errDetail;
                errorBox.style.display = 'block';
                errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerText = "Retry Generation 🚀";
            }
            if (typeof showToast === 'function') {
                showToast(errDetail, "error");
            }
            return data;
        }

        // Response succeeded (200 OK)
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerText = "Regenerate Answer 🚀";
        }

        // Determine whether real AI generated it or if it is development mock awaiting ai.generator
        const answerText = data.answer_text || data.answer || "";
        const isMockAwaiting = typeof answerText === 'string' && answerText.includes('[MOCK DATA');

        // Populate Result Fields
        renderAnswerResult(data, isMockAwaiting);

        if (typeof showToast === 'function') {
            if (isMockAwaiting) {
                showToast("Response received from backend (AI module pending).", "info");
            } else {
                showToast("Answer generated successfully!", "success");
            }
        }

        return data;

    } catch (err) {
        console.error('Answer generation network or execution error:', err);
        if (loadingBox) loadingBox.classList.remove('active');
        if (errorBox) {
            if (errorMessage) errorMessage.innerText = err.message || "Network connection error while reaching answers API.";
            errorBox.style.display = 'block';
            errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerText = "Retry Generation 🚀";
        }
        if (typeof showToast === 'function') {
            showToast("Network error contacting answer generation service.", "error");
        }
    }
}

/**
 * Backward compatibility alias for prepareGeneration
 */
function prepareGeneration() {
    return generateAnswer();
}

/**
 * Renders the returned answer data into the result container
 */
function renderAnswerResult(data, isMockAwaiting) {
    const resultContainer = document.getElementById('generation-result-container');
    const resultHeading = document.getElementById('result-heading');
    const resultBadges = document.getElementById('result-badges');
    const pendingBanner = document.getElementById('ai-pending-banner');
    const answerTextEl = document.getElementById('result-answer-text');
    const sourceRefEl = document.getElementById('result-source-reference');
    const sourceVerifiedEl = document.getElementById('result-source-verified');
    const keywordsVerifiedEl = document.getElementById('result-keywords-verified');
    const approvalStatusEl = document.getElementById('result-approval-status');
    const answerIdEl = document.getElementById('result-answer-id');
    const paramsEl = document.getElementById('result-parameters');
    const footerNoteEl = document.getElementById('result-footer-note');

    if (!resultContainer) return;

    const escape = (typeof escapeHTML === 'function') ? escapeHTML : (s => String(s ?? ''));

    // Check Legitimate UI States:
    // If isMockAwaiting: UI State = "Generation unavailable/pending"
    // If !isMockAwaiting: UI State = "Successfully generated"
    if (isMockAwaiting) {
        if (resultHeading) resultHeading.innerText = "Structured Answer (AI Pipeline Pending)";
        if (pendingBanner) pendingBanner.style.display = 'block';
        if (resultBadges) {
            resultBadges.innerHTML = `
                <span class="badge badge-warning">AI Pipeline Pending</span>
                <span class="badge ${data.approval_status === 'approved' ? 'badge-success' : 'badge-warning'}">${capitalize(data.approval_status)}</span>
            `;
        }
        if (footerNoteEl) footerNoteEl.innerText = "Backend Development Response • Awaiting ai.generator implementation";
    } else {
        if (resultHeading) resultHeading.innerText = "✨ Grounded Answer (AI Generated)";
        if (pendingBanner) pendingBanner.style.display = 'none';
        if (resultBadges) {
            resultBadges.innerHTML = `
                <span class="badge badge-success">AI Generated</span>
                <span class="badge ${data.approval_status === 'approved' ? 'badge-success' : 'badge-warning'}">${capitalize(data.approval_status)}</span>
            `;
        }
        if (footerNoteEl) footerNoteEl.innerText = "Syllabus-aligned answer grounded in teacher-uploaded course materials.";
    }

    // Populate returned fields
    if (answerTextEl) {
        answerTextEl.textContent = data.answer_text || data.answer || "No answer content returned.";
    }
    if (sourceRefEl) {
        sourceRefEl.textContent = data.source_reference || "None";
    }
    if (sourceVerifiedEl) {
        sourceVerifiedEl.innerHTML = data.source_verified 
            ? '<span class="badge badge-success">✓ Grounded</span>' 
            : '<span class="badge badge-warning">Unverified</span>';
    }
    if (keywordsVerifiedEl) {
        keywordsVerifiedEl.innerHTML = data.keywords_verified 
            ? '<span class="badge badge-success">✓ Grounded</span>' 
            : '<span class="badge badge-warning">Unchecked</span>';
    }
    if (approvalStatusEl) {
        const isApproved = data.approval_status === 'approved';
        approvalStatusEl.innerHTML = `
            <span class="badge ${isApproved ? 'badge-success' : 'badge-warning'}">
                ${capitalize(data.approval_status || 'pending')}
            </span>
        `;
    }
    if (answerIdEl) {
        answerIdEl.textContent = `#${data.answer_id ?? '—'} (Topic ID: ${data.topic_id ?? '—'})`;
    }
    if (paramsEl) {
        paramsEl.textContent = `${data.marks ?? '—'} Marks • ${capitalize(data.level)} • ${capitalize(data.language)} • ${data.mode}`;
    }

    resultContainer.style.display = 'block';
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

/**
 * Export current learning configuration object
 */
function getLearningConfig() {
    return {
        courseId: learningConfig.courseId,
        unitId: learningConfig.unitId,
        topicId: learningConfig.topicId,
        level: learningConfig.level,
        language: learningConfig.language,
        marks: learningConfig.marks,
        mode: learningConfig.mode
    };
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/* =========================================================
   MCQ Assessment, Weak Topic & Revision Flow
   ========================================================= */

let currentAssessmentId = null;
let currentQuestions = [];
let currentAssessmentTopicId = null;

/**
 * Initiates MCQ assessment generation for the currently selected topic
 */
async function startMcqAssessment(topicIdOverride) {
    const topicId = topicIdOverride ? parseInt(topicIdOverride, 10) : (learningConfig.topicId ? parseInt(learningConfig.topicId, 10) : null);

    if (!topicId || isNaN(topicId)) {
        if (typeof showToast === 'function') {
            showToast("Please select a Topic to generate an assessment.", "warning");
        }
        return;
    }

    currentAssessmentTopicId = topicId;
    currentAssessmentId = null;
    currentQuestions = [];

    const assessmentCard = document.getElementById('assessment-card');
    const loadingBox = document.getElementById('assessment-loading');
    const quizContainer = document.getElementById('assessment-quiz-container');
    const resultContainer = document.getElementById('assessment-result-container');
    const errorBox = document.getElementById('assessment-error-box');
    const badge = document.getElementById('assessment-badge');
    const unansweredAlert = document.getElementById('assessment-unanswered-alert');

    if (assessmentCard) assessmentCard.style.display = 'block';
    if (errorBox) errorBox.style.display = 'none';
    if (quizContainer) quizContainer.style.display = 'none';
    if (resultContainer) resultContainer.style.display = 'none';
    if (unansweredAlert) unansweredAlert.style.display = 'none';
    if (loadingBox) {
        loadingBox.style.display = 'block';
        loadingBox.classList.add('active');
        loadingBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    if (badge) badge.innerText = "Generating...";

    try {
        const res = await fetch(`${STUDENT_API_BASE}/assessment/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic_id: topicId,
                num_questions: 3
            })
        });

        const data = await res.json();
        if (loadingBox) {
            loadingBox.style.display = 'none';
            loadingBox.classList.remove('active');
        }

        if (!res.ok) {
            const errMsg = (data && data.error) ? data.error : `HTTP ${res.status}: Failed to generate assessment`;
            if (errorBox) {
                const msgEl = document.getElementById('assessment-error-message');
                if (msgEl) msgEl.innerText = errMsg;
                errorBox.style.display = 'block';
                errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            if (badge) badge.innerText = "Error";
            if (typeof showToast === 'function') {
                showToast(errMsg, "error");
            }
            return data;
        }

        currentAssessmentId = data.assessment_id;
        currentQuestions = Array.isArray(data.questions) ? data.questions : [];

        if (currentQuestions.length === 0) {
            if (errorBox) {
                const msgEl = document.getElementById('assessment-error-message');
                if (msgEl) msgEl.innerText = "No questions returned for this topic.";
                errorBox.style.display = 'block';
            }
            if (badge) badge.innerText = "No Questions";
            return data;
        }

        renderQuizQuestions(currentQuestions);

        if (quizContainer) quizContainer.style.display = 'block';
        if (badge) badge.innerText = `${currentQuestions.length} Questions`;
        if (assessmentCard) assessmentCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

        if (typeof showToast === 'function') {
            showToast("Assessment questions ready. Select an answer for each question.", "success");
        }

        return data;

    } catch (err) {
        console.error('Error generating assessment:', err);
        if (loadingBox) {
            loadingBox.style.display = 'none';
            loadingBox.classList.remove('active');
        }
        if (errorBox) {
            const msgEl = document.getElementById('assessment-error-message');
            if (msgEl) msgEl.innerText = err.message || "Network error contacting assessment API.";
            errorBox.style.display = 'block';
            errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (badge) badge.innerText = "Network Error";
        if (typeof showToast === 'function') {
            showToast("Network error contacting assessment API.", "error");
        }
    }
}

/**
 * Renders the question list dynamically without exposing correct answers
 */
function renderQuizQuestions(questions) {
    const listEl = document.getElementById('assessment-questions-list');
    if (!listEl) return;

    listEl.innerHTML = '';
    const escape = (typeof escapeHTML === 'function') ? escapeHTML : (s => String(s ?? ''));

    questions.forEach((q, idx) => {
        const qCard = document.createElement('div');
        qCard.className = 'mcq-question-card';
        qCard.id = `mcq-q-${q.question_id}`;

        const qTitle = document.createElement('div');
        qTitle.className = 'mcq-question-text';
        qTitle.innerHTML = `<strong>Q${idx + 1}.</strong> ${escape(q.question_text)}`;
        qCard.appendChild(qTitle);

        const optionsGroup = document.createElement('div');
        optionsGroup.className = 'mcq-options-group';

        const options = Array.isArray(q.options) ? q.options : [];
        options.forEach(opt => {
            const optLabel = document.createElement('label');
            optLabel.className = 'mcq-option-label';

            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = `question_${q.question_id}`;
            radio.value = opt;

            const span = document.createElement('span');
            span.textContent = opt;

            optLabel.appendChild(radio);
            optLabel.appendChild(span);

            radio.addEventListener('change', () => {
                optionsGroup.querySelectorAll('.mcq-option-label').forEach(l => {
                    l.style.borderColor = 'var(--border-color)';
                    l.style.backgroundColor = '#ffffff';
                });
                if (radio.checked) {
                    optLabel.style.borderColor = 'var(--primary-color)';
                    optLabel.style.backgroundColor = '#f0f9ff';
                }
            });

            optionsGroup.appendChild(optLabel);
        });

        qCard.appendChild(optionsGroup);
        listEl.appendChild(qCard);
    });
}

/**
 * Submits the student's selected MCQ answers to POST /api/assessment/submit
 */
async function submitAssessment() {
    if (!currentAssessmentId) {
        if (typeof showToast === 'function') {
            showToast("Assessment session not found. Please regenerate assessment.", "error");
        }
        return;
    }

    const answers = {};
    let unansweredCount = 0;

    currentQuestions.forEach(q => {
        const selected = document.querySelector(`input[name="question_${q.question_id}"]:checked`);
        if (selected) {
            answers[String(q.question_id)] = selected.value;
        } else {
            unansweredCount++;
        }
    });

    const unansweredAlert = document.getElementById('assessment-unanswered-alert');

    if (unansweredCount > 0) {
        if (unansweredAlert) {
            unansweredAlert.style.display = 'block';
            unansweredAlert.innerText = `⚠️ Please select an answer for all questions (${unansweredCount} remaining) before submitting.`;
            unansweredAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (typeof showToast === 'function') {
            showToast(`Please answer all ${currentQuestions.length} questions before submitting.`, "warning");
        }
        return;
    } else {
        if (unansweredAlert) unansweredAlert.style.display = 'none';
    }

    const submitBtn = document.getElementById('btn-submit-mcq');
    const quizContainer = document.getElementById('assessment-quiz-container');
    const resultContainer = document.getElementById('assessment-result-container');
    const errorBox = document.getElementById('assessment-error-box');

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = "Submitting & Grading...";
    }
    if (errorBox) errorBox.style.display = 'none';

    try {
        const res = await fetch(`${STUDENT_API_BASE}/assessment/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                assessment_id: parseInt(currentAssessmentId, 10),
                answers: answers
            })
        });

        const data = await res.json();

        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = "Submit Assessment 📤";
        }

        if (!res.ok) {
            const errMsg = (data && data.error) ? data.error : `HTTP ${res.status}: Failed to submit assessment`;
            if (errorBox) {
                const msgEl = document.getElementById('assessment-error-message');
                if (msgEl) msgEl.innerText = errMsg;
                errorBox.style.display = 'block';
                errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            if (typeof showToast === 'function') {
                showToast(errMsg, "error");
            }
            return data;
        }

        if (quizContainer) quizContainer.style.display = 'none';
        renderAssessmentResults(data);

        if (resultContainer) {
            resultContainer.style.display = 'block';
            resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        if (typeof showToast === 'function') {
            if (data.is_weak) {
                showToast("Assessment complete: Weak topic flagged for revision.", "warning");
            } else {
                showToast(`Assessment complete: Scored ${data.score}/${data.total_questions}!`, "success");
            }
        }

        await loadWeakTopics();

        return data;

    } catch (err) {
        console.error('Error submitting assessment:', err);
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = "Submit Assessment 📤";
        }
        if (errorBox) {
            const msgEl = document.getElementById('assessment-error-message');
            if (msgEl) msgEl.innerText = err.message || "Network error submitting assessment.";
            errorBox.style.display = 'block';
            errorBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (typeof showToast === 'function') {
            showToast("Network error submitting assessment.", "error");
        }
    }
}

/**
 * Renders the assessment outcome: score, percentage, recommendation, weak topic status, and per-question breakdown
 */
function renderAssessmentResults(data) {
    const summaryBox = document.getElementById('assessment-score-summary');
    const reviewList = document.getElementById('assessment-review-list');
    const revisionWrapper = document.getElementById('revision-action-container');
    const badge = document.getElementById('assessment-badge');

    const escape = (typeof escapeHTML === 'function') ? escapeHTML : (s => String(s ?? ''));

    if (badge) {
        badge.innerText = `Score: ${data.score}/${data.total_questions} (${data.percentage}%)`;
        badge.className = data.is_weak ? 'badge badge-warning' : 'badge badge-success';
    }

    if (summaryBox) {
        summaryBox.innerHTML = `
            <div class="flex justify-between items-center mb-3" style="flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <h4 style="margin: 0 0 0.25rem 0;">Assessment Score: ${data.score} / ${data.total_questions} (${data.percentage}%)</h4>
                    <p class="text-secondary" style="margin: 0; font-size: 0.875rem;">
                        ${escape(data.recommendation || (data.is_weak ? 'Revision recommended' : 'Good mastery of topic'))}
                    </p>
                </div>
                <div>
                    ${data.is_weak 
                        ? '<span class="badge badge-danger">⚠️ Weak Topic Flagged</span>' 
                        : '<span class="badge badge-success">✓ Mastery Achieved</span>'}
                </div>
            </div>
            ${data.is_weak ? `
                <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: var(--radius-md); padding: 0.85rem 1rem; margin-top: 0.75rem; font-size: 0.875rem; color: #92400e;">
                    <strong>Revision Recommended:</strong> Your score was below the 60% threshold. This topic has been logged to your Weak Topics list. Click "Revise Topic" below to review teacher-approved notes and solidify your understanding.
                </div>
            ` : `
                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: var(--radius-md); padding: 0.85rem 1rem; margin-top: 0.75rem; font-size: 0.875rem; color: #166534;">
                    <strong>Excellent Performance!</strong> You have demonstrated a solid understanding of the concepts in this topic.
                </div>
            `}
        `;
    }

    if (reviewList && Array.isArray(data.results)) {
        reviewList.innerHTML = '';
        data.results.forEach((r, idx) => {
            const card = document.createElement('div');
            card.className = `mcq-review-card ${r.is_correct ? 'correct' : 'incorrect'}`;

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; gap: 0.5rem;">
                    <div style="font-weight: 600; font-size: 0.9375rem;">
                        Q${idx + 1}. ${escape(r.question_text)}
                    </div>
                    <div>
                        ${r.is_correct 
                            ? '<span class="badge badge-success">Correct (+1)</span>' 
                            : '<span class="badge badge-danger">Incorrect (0)</span>'}
                    </div>
                </div>
                <div style="font-size: 0.875rem; margin-bottom: 0.35rem;">
                    <strong>Your Answer:</strong> <span style="color: ${r.is_correct ? 'var(--success-color)' : 'var(--danger-color)'}; font-weight: 500;">${escape(r.selected_option || 'None')}</span>
                </div>
                ${!r.is_correct ? `
                    <div style="font-size: 0.875rem; color: var(--success-color);">
                        <strong>Correct Answer:</strong> <span style="font-weight: 500;">${escape(r.correct_answer)}</span>
                    </div>
                ` : ''}
            `;

            reviewList.appendChild(card);
        });
    }

    if (revisionWrapper) {
        if (data.is_weak) {
            revisionWrapper.innerHTML = `
                <button type="button" class="btn btn-warning" id="btn-revise-topic" onclick="reviseTopic(${data.topic_id})" style="font-weight: 600;">
                    Revise Topic ↺
                </button>
            `;
        } else {
            revisionWrapper.innerHTML = '';
        }
    }
}

/**
 * Closes assessment panel and returns to learning workspace
 */
function cancelAssessment() {
    const assessmentCard = document.getElementById('assessment-card');
    if (assessmentCard) assessmentCard.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Handles the "Revise Topic" action:
 * Returns the student to the learning flow with the weak topic selected
 */
function reviseTopic(topicId, courseId, unitId) {
    const tId = parseInt(topicId, 10);
    if (isNaN(tId)) return;

    // Check if on dashboard.html: redirect to learning.html with topic selected
    if (document.getElementById('student-dashboard-root')) {
        const cId = courseId || 1;
        window.location.href = `learning.html?course_id=${cId}&topic_id=${tId}&mode=learn_simply&level=basic`;
        return;
    }

    // Currently on learning.html: update state and navigate to setup
    learningConfig.topicId = tId;
    learningConfig.mode = "learn_simply"; // Default to Learn Simply for revision

    const topicSelect = document.getElementById('student-topic-select');
    if (topicSelect) {
        topicSelect.value = String(tId);
    }

    syncPillsToUI();
    updateSummaryAndReadiness();

    const assessmentCard = document.getElementById('assessment-card');
    if (assessmentCard) assessmentCard.style.display = 'none';

    const setupCard = document.getElementById('setup-main-card');
    if (setupCard) {
        setupCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    if (typeof showToast === 'function') {
        showToast("Revision Mode: Topic selected for review. Review grounded concepts.", "info");
    }
}

/**
 * Fetches and displays weak topics from GET /api/assessment/weak-topics
 */
async function loadWeakTopics() {
    const dashboardContainer = document.getElementById('dashboard-weak-topics-container');
    const badge = document.getElementById('weak-topics-count');

    if (!dashboardContainer && !badge) return;

    try {
        const res = await fetch(`${STUDENT_API_BASE}/assessment/weak-topics`);
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        const weakTopics = await res.json();
        const list = Array.isArray(weakTopics) ? weakTopics : [];

        if (badge) {
            badge.innerText = `${list.length} Topics`;
            badge.className = list.length > 0 ? 'badge badge-warning' : 'badge badge-success';
        }

        if (dashboardContainer) {
            if (list.length === 0) {
                dashboardContainer.innerHTML = `
                    <div class="text-secondary" style="padding: 1.5rem 0; text-align: center; font-size: 0.875rem;">
                        🎉 No weak topics flagged! Keep taking assessments to test your understanding.
                    </div>
                `;
                return;
            }

            const escape = (typeof escapeHTML === 'function') ? escapeHTML : (s => String(s ?? ''));
            dashboardContainer.innerHTML = '';

            list.forEach(wt => {
                const item = document.createElement('div');
                item.className = 'weak-topic-item';

                const pct = wt.total > 0 ? Math.round((wt.score / wt.total) * 100) : 0;

                item.innerHTML = `
                    <div>
                        <div style="font-weight: 600; font-size: 0.95rem; color: var(--text-primary);">
                            ${escape(wt.topic_name)}
                        </div>
                        <div class="text-secondary" style="font-size: 0.8125rem; margin-top: 0.2rem;">
                            Course ID: ${wt.course_id} • Unit ${wt.unit_number}: ${escape(wt.unit_name)}
                        </div>
                        <div style="font-size: 0.75rem; margin-top: 0.35rem; color: var(--text-secondary);">
                            Recent Assessment Score: <strong>${wt.score} / ${wt.total} (${pct}%)</strong>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="badge badge-danger">Needs Revision</span>
                        <button type="button" class="btn btn-warning" onclick="reviseTopic(${wt.topic_id}, ${wt.course_id})" style="font-size: 0.8125rem; padding: 0.4rem 0.85rem; font-weight: 600;">
                            Revise Topic ↺
                        </button>
                    </div>
                `;

                dashboardContainer.appendChild(item);
            });
        }

    } catch (err) {
        console.error('Failed to load weak topics:', err);
        if (dashboardContainer) {
            dashboardContainer.innerHTML = `
                <div style="color: var(--danger-color); font-size: 0.875rem; padding: 1rem 0;">
                    Unable to load weak topics from server.
                </div>
            `;
        }
        if (badge) badge.innerText = "Error";
    }
}

// Attach to window for test verification & cross-module integration
if (typeof window !== 'undefined') {
    window.learningConfig = learningConfig;
    window.getLearningConfig = getLearningConfig;
    window.isConfigurationValid = isConfigurationValid;
    window.generateAnswer = generateAnswer;
    window.prepareGeneration = prepareGeneration;
    window.startMcqAssessment = startMcqAssessment;
    window.submitAssessment = submitAssessment;
    window.cancelAssessment = cancelAssessment;
    window.reviseTopic = reviseTopic;
    window.loadWeakTopics = loadWeakTopics;
}

/* =========================================================
   Student Dashboard Logic (dashboard.html)
   ========================================================= */

function initStudentDashboard() {
    const demoBtn = document.getElementById('btn-dashboard-demo');
    if (demoBtn) {
        demoBtn.addEventListener('click', () => {
            window.location.href = "learning.html?course_id=1&unit_id=1&topic_id=1&level=intermediate&lang=english&marks=5&mode=exam_answer";
        });
    }
    loadWeakTopics();
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
