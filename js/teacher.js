/**
 * Teacher-specific interactions & Backend API Integration
 */

const TEACHER_API_BASE = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : '/api';

/* =========================================================
   Course Builder Logic (teacher/course.html)
   ========================================================= */
let unitCounter = 0;
let topicCounters = {};

function addUnit() {
    unitCounter++;
    topicCounters[unitCounter] = 0;
    
    const container = document.getElementById('units-container');
    if (!container) return;

    const unitHTML = `
        <div class="unit-card" id="unit-${unitCounter}" data-unit-idx="${unitCounter}">
            <div class="unit-header">
                <input type="text" class="unit-title-input" value="Unit ${unitCounter}: New Unit" placeholder="Unit Name">
                <div class="flex gap-2">
                    <button type="button" class="btn btn-secondary" onclick="addTopic(${unitCounter})">
                        + Add Topic
                    </button>
                    <button type="button" class="btn btn-danger" onclick="removeUnit(${unitCounter})">
                        Remove
                    </button>
                </div>
            </div>
            <div class="topics-container" id="topics-unit-${unitCounter}">
                <!-- Topics go here -->
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', unitHTML);
    addTopic(unitCounter); // Add an initial topic
    if (typeof showToast === 'function') {
        showToast('New unit added', 'info');
    }
}

function removeUnit(unitId) {
    const unit = document.getElementById(`unit-${unitId}`);
    if (unit) {
        unit.remove();
        if (typeof showToast === 'function') {
            showToast('Unit removed', 'info');
        }
    }
}

function addTopic(unitId) {
    if (!topicCounters[unitId]) {
        topicCounters[unitId] = 0;
    }
    topicCounters[unitId]++;
    const topicId = topicCounters[unitId];
    
    const container = document.getElementById(`topics-unit-${unitId}`);
    if (!container) return;

    const topicHTML = `
        <div class="topic-item" id="topic-${unitId}-${topicId}">
            <span>📄</span>
            <input type="text" class="topic-title-input" value="Topic ${topicId}: New Topic" placeholder="Topic Name">
            <button type="button" class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="removeTopic(${unitId}, ${topicId})">
                ✕
            </button>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', topicHTML);
}

function removeTopic(unitId, topicId) {
    const topic = document.getElementById(`topic-${unitId}-${topicId}`);
    if (topic) {
        topic.remove();
    }
}

async function saveCourse() {
    const titleInput = document.getElementById('course-title');
    const descInput = document.getElementById('course-description');
    const saveBtn = document.getElementById('save-course-btn');

    const courseTitle = titleInput ? titleInput.value.trim() : '';
    const description = descInput ? descInput.value.trim() : '';

    if (!courseTitle) {
        if (typeof showToast === 'function') {
            showToast('Please enter a course title.', 'error');
        } else {
            alert('Please enter a course title.');
        }
        return;
    }

    // Check units
    const unitCards = document.querySelectorAll('#units-container .unit-card');
    if (unitCards.length === 0) {
        if (typeof showToast === 'function') {
            showToast('Please add at least one unit.', 'warning');
        }
        return;
    }

    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerText = 'Saving Course...';
    }

    try {
        // Step 1: Create Course (API expects {"course_name": ..., "description": ...})
        const courseRes = await fetch(`${TEACHER_API_BASE}/courses`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                course_name: courseTitle,
                description: description
            })
        });

        const courseData = await courseRes.json();
        if (!courseRes.ok) {
            throw new Error(courseData.error || 'Failed to create course');
        }

        const courseId = courseData.course_id || (courseData.course && courseData.course.course_id);

        // Step 2 & 3: Iterate through units and topics
        let unitSeq = 1;
        for (const unitCard of unitCards) {
            const unitTitleInput = unitCard.querySelector('.unit-title-input');
            const unitName = unitTitleInput ? unitTitleInput.value.trim() : `Unit ${unitSeq}`;

            // API expects {"unit_number": unitSeq, "unit_name": unitName}
            const unitRes = await fetch(`${TEACHER_API_BASE}/courses/${courseId}/units`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ unit_number: unitSeq, unit_name: unitName })
            });

            const unitData = await unitRes.json();
            if (!unitRes.ok) {
                throw new Error(unitData.error || `Failed to create Unit ${unitSeq}`);
            }

            const unitId = unitData.unit_id || (unitData.unit && unitData.unit.unit_id);

            // Find all topics in this unit card
            const topicInputs = unitCard.querySelectorAll('.topic-title-input');
            for (const topicInput of topicInputs) {
                const topicName = topicInput.value.trim();
                if (topicName) {
                    // API expects {"topic_name": topicName}
                    const topicRes = await fetch(`${TEACHER_API_BASE}/units/${unitId}/topics`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ topic_name: topicName })
                    });
                    const topicData = await topicRes.json();
                    if (!topicRes.ok) {
                        throw new Error(topicData.error || `Failed to create topic "${topicName}"`);
                    }
                }
            }
            unitSeq++;
        }

        if (typeof showToast === 'function') {
            showToast('Course, units, and topics saved successfully!', 'success');
        }

        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1200);

    } catch (err) {
        console.error('Error saving course:', err);
        if (typeof showToast === 'function') {
            showToast(`Error: ${err.message}`, 'error');
        } else {
            alert(`Error: ${err.message}`);
        }
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerText = 'Save Course';
        }
    }
}

/* =========================================================
   Materials Upload Logic (teacher/materials.html)
   ========================================================= */

let coursesMap = {};

async function loadCoursesForUpload() {
    const courseSelect = document.getElementById('course-select');
    if (!courseSelect) return;

    try {
        const res = await fetch(`${TEACHER_API_BASE}/courses`);
        const data = await res.json();
        const courseList = Array.isArray(data) ? data : (data.courses || []);

        if (res.ok && courseList.length > 0) {
            courseSelect.innerHTML = '<option value="">Select Course</option>';
            courseList.forEach(c => {
                const cId = c.course_id;
                const cName = c.course_name || c.title;
                coursesMap[cId] = cName;
                const opt = document.createElement('option');
                opt.value = cId;
                opt.textContent = `${cName} (ID: ${cId})`;
                courseSelect.appendChild(opt);
            });
        } else {
            courseSelect.innerHTML = '<option value="">No courses available. Create a course first.</option>';
        }
    } catch (err) {
        console.error('Failed to load courses for upload dropdown:', err);
        courseSelect.innerHTML = '<option value="">Error loading courses</option>';
    }

    courseSelect.addEventListener('change', async () => {
        const courseId = courseSelect.value;
        const unitSelect = document.getElementById('unit-select');
        const topicSelect = document.getElementById('topic-select');

        if (unitSelect) {
            unitSelect.innerHTML = '<option value="">Select Unit (Optional)</option>';
            unitSelect.disabled = !courseId;
        }
        if (topicSelect) {
            topicSelect.innerHTML = '<option value="">Select Topic (Optional)</option>';
            topicSelect.disabled = true;
        }

        if (!courseId || !unitSelect) return;

        try {
            // Fetch course with units & topics via GET /api/courses/<id>
            const res = await fetch(`${TEACHER_API_BASE}/courses/${courseId}`);
            const data = await res.json();
            if (res.ok && data && data.units && data.units.length > 0) {
                window._currentCourseUnits = data.units;
                data.units.forEach(u => {
                    const opt = document.createElement('option');
                    opt.value = u.unit_id;
                    opt.textContent = u.unit_name || u.title || `Unit ${u.unit_number}`;
                    unitSelect.appendChild(opt);
                });
                unitSelect.disabled = false;
            } else {
                unitSelect.innerHTML = '<option value="">No units found for this course</option>';
            }
        } catch (err) {
            console.error('Failed to load course details and units:', err);
        }
    });

    const unitSelect = document.getElementById('unit-select');
    if (unitSelect) {
        unitSelect.addEventListener('change', () => {
            const unitId = unitSelect.value;
            const topicSelect = document.getElementById('topic-select');
            if (!topicSelect) return;
            topicSelect.innerHTML = '<option value="">Select Topic (Optional)</option>';

            if (!unitId || !window._currentCourseUnits) {
                topicSelect.disabled = true;
                return;
            }

            const selectedUnit = window._currentCourseUnits.find(u => String(u.unit_id) === String(unitId));
            if (selectedUnit && selectedUnit.topics && selectedUnit.topics.length > 0) {
                selectedUnit.topics.forEach(t => {
                    const opt = document.createElement('option');
                    opt.value = t.topic_id;
                    opt.textContent = t.topic_name || t.title;
                    topicSelect.appendChild(opt);
                });
                topicSelect.disabled = false;
            } else {
                topicSelect.innerHTML = '<option value="">No topics in this unit</option>';
            }
        });
    }
}

async function loadMaterials() {
    const list = document.getElementById('material-list');
    if (!list) return;

    try {
        const res = await fetch(`${TEACHER_API_BASE}/materials`);
        const data = await res.json();
        if (!res.ok) {
            list.innerHTML = '<div style="color:var(--danger); padding:1rem; text-align:center;">Failed to load materials.</div>';
            return;
        }

        const materials = Array.isArray(data) ? data : (data.materials || []);
        if (materials.length === 0) {
            list.innerHTML = '<div style="color:var(--text-secondary); padding:1.5rem; text-align:center;">No materials uploaded yet.</div>';
            return;
        }

        list.innerHTML = '';
        materials.forEach(mat => {
            let badgeClass = 'badge-secondary';
            let badgeText = mat.processing_status || 'Unknown';
            let subText = '';

            if (mat.processing_status === 'processed') {
                badgeClass = 'badge-success';
                badgeText = 'Processed';
                subText = 'Extracted & Ready';
            } else if (mat.processing_status === 'pending') {
                badgeClass = 'badge-warning';
                badgeText = 'Queued (Pending AI)';
                subText = 'Processing queued';
            } else if (mat.processing_status === 'failed') {
                badgeClass = 'badge-danger';
                badgeText = 'Failed';
                subText = 'Processing failed';
            }

            const fileName = mat.file_name || mat.filename || `Document #${mat.material_id}`;
            const courseName = coursesMap[mat.course_id] ? `${coursesMap[mat.course_id]} (ID: ${mat.course_id})` : `Course ID: ${mat.course_id}`;
            const uploadedAt = mat.uploaded_at ? ` • ${mat.uploaded_at}` : '';

            const itemHTML = `
                <div class="material-item" id="mat-${mat.material_id}">
                    <div class="material-info">
                        <span class="material-icon">📄</span>
                        <div>
                            <div style="font-weight:500;">${fileName}</div>
                            <div style="font-size:0.75rem;color:var(--text-secondary);">${courseName}${uploadedAt} • ${subText}</div>
                        </div>
                    </div>
                    <span class="badge ${badgeClass}" id="badge-${mat.material_id}">${badgeText}</span>
                </div>
            `;
            list.insertAdjacentHTML('beforeend', itemHTML);
        });

    } catch (err) {
        console.error('Error loading materials:', err);
        list.innerHTML = '<div style="color:var(--danger); padding:1rem; text-align:center;">Error connecting to materials server.</div>';
    }
}

function setupFileUpload() {
    const dropZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-upload');
    if (!dropZone || !fileInput) return;

    // Click to upload
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length) {
            handleFiles(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length) {
            handleFiles(fileInput.files);
            fileInput.value = '';
        }
    });
}

async function handleFiles(files) {
    if (!files || !files.length) {
        if (typeof showToast === 'function') {
            showToast('No file selected.', 'warning');
        }
        return;
    }

    const file = files[0];
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        if (typeof showToast === 'function') {
            showToast('Please upload a valid PDF file.', 'error');
        } else {
            alert('Please upload a valid PDF file.');
        }
        return;
    }
    
    const courseSelect = document.getElementById('course-select');
    const courseId = courseSelect ? courseSelect.value : '';
    
    if (!courseId) {
        if (typeof showToast === 'function') {
            showToast('Please select a Course first.', 'warning');
        } else {
            alert('Please select a Course first.');
        }
        return;
    }

    await uploadAndProcessMaterial(file, courseId);
}

async function uploadAndProcessMaterial(file, courseId) {
    if (typeof showToast === 'function') {
        showToast(`Uploading ${file.name}...`, 'info');
    }

    const formData = new FormData();
    formData.append('course_id', courseId);
    formData.append('file', file);

    let materialId = null;

    try {
        // Step 1: Upload material to POST /api/materials/upload
        const uploadRes = await fetch(`${TEACHER_API_BASE}/materials/upload`, {
            method: 'POST',
            body: formData
        });

        const uploadData = await uploadRes.json();
        if (!uploadRes.ok) {
            throw new Error(uploadData.error || 'Upload failed');
        }

        materialId = uploadData.material_id || (uploadData.material && uploadData.material.material_id);
        if (typeof showToast === 'function') {
            showToast('PDF uploaded successfully! Triggering processing...', 'success');
        }

        // Refresh material list immediately to show newly uploaded pending item
        await loadMaterials();

    } catch (err) {
        console.error('Material upload error:', err);
        if (typeof showToast === 'function') {
            showToast(`Upload failed: ${err.message}`, 'error');
        } else {
            alert(`Upload failed: ${err.message}`);
        }
        return;
    }

    if (!materialId) return;

    try {
        // Step 2: Trigger material processing via POST /api/materials/<material_id>/process
        const processRes = await fetch(`${TEACHER_API_BASE}/materials/${materialId}/process`, {
            method: 'POST'
        });
        const processData = await processRes.json();

        if (!processRes.ok) {
            throw new Error(processData.error || 'Processing request failed');
        }

        if (processData.processing_status === 'pending') {
            if (typeof showToast === 'function') {
                showToast('Material queued for processing (AI module pending).', 'warning');
            }
        } else if (processData.processing_status === 'processed') {
            if (typeof showToast === 'function') {
                showToast('Material processed successfully!', 'success');
            }
        } else if (processData.processing_status === 'failed') {
            if (typeof showToast === 'function') {
                showToast('Material processing failed.', 'error');
            }
        }

        // Refresh material list with updated status
        await loadMaterials();

    } catch (err) {
        console.error('Material process error:', err);
        if (typeof showToast === 'function') {
            showToast(`Processing error: ${err.message}`, 'error');
        }
        await loadMaterials();
    }
}

/* =========================================================
   Review Logic (teacher/review.html)
   ========================================================= */

async function loadPendingReviews() {
    const container = document.getElementById('review-cards-container');
    const badge = document.getElementById('pending-reviews-badge');
    if (!container) return;

    container.innerHTML = '<div style="padding:2rem; text-align:center; color:var(--text-secondary);">Loading pending reviews from database...</div>';

    try {
        const res = await fetch(`${TEACHER_API_BASE}/answers?approval_status=pending`);
        const data = await res.json();

        if (!res.ok) {
            container.innerHTML = `<div style="color:var(--danger-color); padding:1rem; text-align:center;">Failed to load answers: ${data.error || 'Server error'}</div>`;
            return;
        }

        const answers = Array.isArray(data) ? data : (data.answers || []);
        if (badge) {
            badge.innerText = `${answers.length} Pending`;
        }

        if (answers.length === 0) {
            container.innerHTML = `
                <div class="card" style="padding: 2.5rem; text-align: center; color: var(--text-secondary);">
                    <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🎉</div>
                    <h3 style="margin-bottom: 0.5rem; color: var(--text-primary);">No Pending Reviews</h3>
                    <p>All answers have been approved or rejected.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        answers.forEach(ans => {
            const rawContent = ans.answer_text || ans.answer || '(Empty answer content)';
            const formattedContent = rawContent.replace(/\n/g, '<br>');
            const sourceRef = ans.source_reference
                ? `<div style="font-size:0.8rem; color:var(--text-secondary); margin-top:0.75rem; padding-top:0.5rem; border-top:1px dashed var(--border-color);"><strong>Source Reference:</strong> ${ans.source_reference}</div>`
                : '';
            const verificationInfo = `Source Verified: ${ans.source_verified ? '✓ Yes' : '✗ No'} • Keywords Verified: ${ans.keywords_verified ? '✓ Yes' : '✗ No'}`;

            const cardHTML = `
                <div class="card review-card" id="review-${ans.answer_id}">
                    <div class="review-header">
                        <div>
                            <div class="review-meta" style="margin-bottom:0.25rem;">
                                Topic ID: ${ans.topic_id} • Level: ${ans.level || 'intermediate'} • Language: ${ans.language || 'english'} • ${ans.marks || 5} Marks • Mode: ${ans.mode || 'exam'}
                            </div>
                            <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:0.5rem;">
                                ${verificationInfo}
                            </div>
                            <h3 class="review-title" style="margin:0; font-size:1.125rem;">Answer #${ans.answer_id}</h3>
                        </div>
                        <span class="badge badge-warning" id="status-${ans.answer_id}">Pending Review</span>
                    </div>
                    <div class="review-body review-answer" id="answer-text-${ans.answer_id}">
                        ${formattedContent}
                        ${sourceRef}
                    </div>
                    <div class="review-actions" id="actions-${ans.answer_id}">
                        <button type="button" class="btn btn-secondary" id="edit-btn-${ans.answer_id}" onclick="toggleEditAnswer(${ans.answer_id})">Edit Answer</button>
                        <button type="button" class="btn btn-danger" onclick="rejectAnswer(${ans.answer_id})">Reject</button>
                        <button type="button" class="btn btn-primary" onclick="approveAnswer(${ans.answer_id})">Approve Answer</button>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', cardHTML);
        });

    } catch (err) {
        console.error('Error loading pending reviews:', err);
        container.innerHTML = '<div style="color:var(--danger-color); padding:1rem; text-align:center;">Error connecting to answers server.</div>';
    }
}

async function approveAnswer(id) {
    const card = document.getElementById(`review-${id}`);
    const statusBadge = document.getElementById(`status-${id}`);

    try {
        const res = await fetch(`${TEACHER_API_BASE}/answers/${id}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || 'Failed to approve answer');
        }

        if (card && statusBadge) {
            card.className = 'card review-card approved';
            statusBadge.className = 'badge badge-success';
            statusBadge.innerText = 'Approved';
            removeActionButtons(id);
        }

        if (typeof showToast === 'function') {
            showToast('Answer approved for students.', 'success');
        }

        // Remove processed answer from pending list after confirmation
        setTimeout(async () => {
            if (card) card.remove();
            const remaining = document.querySelectorAll('#review-cards-container .review-card');
            if (remaining.length === 0) {
                await loadPendingReviews();
            } else {
                updatePendingBadgeCount(-1);
            }
        }, 900);

    } catch (err) {
        console.error('Error approving answer:', err);
        if (typeof showToast === 'function') {
            showToast(`Error approving answer: ${err.message}`, 'error');
        }
    }
}

async function rejectAnswer(id) {
    const card = document.getElementById(`review-${id}`);
    const statusBadge = document.getElementById(`status-${id}`);

    try {
        const res = await fetch(`${TEACHER_API_BASE}/answers/${id}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || 'Failed to reject answer');
        }

        if (card && statusBadge) {
            card.className = 'card review-card rejected';
            statusBadge.className = 'badge badge-danger';
            statusBadge.innerText = 'Rejected';
            removeActionButtons(id);
        }

        if (typeof showToast === 'function') {
            showToast('Answer rejected.', 'info');
        }

        // Remove processed answer from pending list after confirmation
        setTimeout(async () => {
            if (card) card.remove();
            const remaining = document.querySelectorAll('#review-cards-container .review-card');
            if (remaining.length === 0) {
                await loadPendingReviews();
            } else {
                updatePendingBadgeCount(-1);
            }
        }, 900);

    } catch (err) {
        console.error('Error rejecting answer:', err);
        if (typeof showToast === 'function') {
            showToast(`Error rejecting answer: ${err.message}`, 'error');
        }
    }
}

function updatePendingBadgeCount(delta) {
    const badge = document.getElementById('pending-reviews-badge');
    if (badge) {
        const currentText = badge.innerText;
        const currentCount = parseInt(currentText, 10);
        if (!isNaN(currentCount)) {
            const nextCount = Math.max(0, currentCount + delta);
            badge.innerText = `${nextCount} Pending`;
        }
    }
}

function toggleEditAnswer(id) {
    const answerDiv = document.getElementById(`answer-text-${id}`);
    const btn = document.getElementById(`edit-btn-${id}`);
    if (!answerDiv || !btn) return;
    
    if (answerDiv.querySelector('textarea')) {
        // Save logic (local draft update)
        const newText = answerDiv.querySelector('textarea').value;
        answerDiv.innerHTML = newText.replace(/\n/g, '<br>');
        btn.innerText = 'Edit Answer';
        if (typeof showToast === 'function') {
            showToast('Answer updated manually in draft.', 'success');
        }
    } else {
        // Edit logic
        const currentText = answerDiv.innerHTML.replace(/<br\s*[\/]?>/gi, '\n').trim();
        answerDiv.innerHTML = `<textarea style="width:100%; min-height:120px; font-family:inherit; font-size:0.9rem; padding:0.5rem; border:1px solid var(--border-color); border-radius:var(--radius-sm);">${currentText}</textarea>`;
        btn.innerText = 'Save Changes';
    }
}

function removeActionButtons(id) {
    const actions = document.getElementById(`actions-${id}`);
    if (actions) {
        actions.style.display = 'none';
    }
}

/* =========================================================
   Teacher Dashboard Logic (teacher/dashboard.html)
   ========================================================= */

async function initTeacherDashboard() {
    const coursesStat = document.getElementById('stat-total-courses');
    const materialsStat = document.getElementById('stat-total-materials');
    const reviewsStat = document.getElementById('stat-pending-reviews');

    if (!coursesStat && !materialsStat && !reviewsStat) return;

    try {
        const coursesRes = await fetch(`${TEACHER_API_BASE}/courses`);
        if (coursesRes.ok) {
            const data = await coursesRes.json();
            const list = Array.isArray(data) ? data : (data.courses || []);
            if (coursesStat) {
                coursesStat.innerText = list.length;
            }
        }
    } catch (err) {
        console.error('Dashboard courses count error:', err);
    }

    try {
        const materialsRes = await fetch(`${TEACHER_API_BASE}/materials`);
        if (materialsRes.ok) {
            const data = await materialsRes.json();
            const list = Array.isArray(data) ? data : (data.materials || []);
            if (materialsStat) {
                materialsStat.innerText = list.length;
            }
        }
    } catch (err) {
        console.error('Dashboard materials count error:', err);
    }

    try {
        const reviewsRes = await fetch(`${TEACHER_API_BASE}/answers?approval_status=pending`);
        if (reviewsRes.ok) {
            const data = await reviewsRes.json();
            const list = Array.isArray(data) ? data : (data.answers || []);
            if (reviewsStat) {
                reviewsStat.innerText = list.length;
            }
        }
    } catch (err) {
        console.error('Dashboard pending reviews count error:', err);
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    // If on teacher dashboard
    if (document.getElementById('stat-total-courses') || document.getElementById('stat-total-materials')) {
        initTeacherDashboard();
    }

    // If on course builder
    if (document.getElementById('units-container')) {
        addUnit();
    }
    
    // If on materials page
    if (document.getElementById('upload-zone')) {
        setupFileUpload();
        loadCoursesForUpload();
        loadMaterials();
    }

    // If on review page
    if (document.getElementById('review-cards-container')) {
        loadPendingReviews();
    }
});
