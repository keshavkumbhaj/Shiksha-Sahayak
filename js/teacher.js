/**
 * Teacher-specific interactions
 */

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
        <div class="unit-card" id="unit-${unitCounter}">
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
    showToast('New unit added', 'success');
}

function removeUnit(unitId) {
    const unit = document.getElementById(`unit-${unitId}`);
    if (unit) {
        unit.remove();
        showToast('Unit removed', 'info');
    }
}

function addTopic(unitId) {
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

function saveCourse() {
    const title = document.getElementById('course-title').value;
    if (!title) {
        showToast('Please enter a course title', 'error');
        return;
    }
    // Logic to serialize data and send to backend would go here
    showToast('Course saved successfully!', 'success');
    setTimeout(() => {
        window.location.href = 'dashboard.html';
    }, 1500);
}

/* =========================================================
   Materials Upload Logic (teacher/materials.html)
   ========================================================= */

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
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFiles(fileInput.files);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFiles(fileInput.files);
        }
    });
}

function handleFiles(files) {
    const file = files[0];
    if (file.type !== 'application/pdf') {
        showToast('Please upload a PDF file.', 'error');
        return;
    }
    
    const course = document.getElementById('course-select').value;
    const unit = document.getElementById('unit-select').value;
    const topic = document.getElementById('topic-select').value;
    
    if(!course || !unit || !topic) {
        showToast('Please select Course, Unit, and Topic first.', 'warning');
        return;
    }

    simulateUploadProcess(file.name);
}

function simulateUploadProcess(filename) {
    showToast(`Uploading ${filename}...`, 'info');
    
    // Create new list item
    const list = document.getElementById('material-list');
    const id = Date.now();
    const itemHTML = `
        <div class="material-item" id="mat-${id}">
            <div class="material-info">
                <span class="material-icon">📄</span>
                <div>
                    <div style="font-weight:500;">${filename}</div>
                    <div style="font-size:0.75rem;color:var(--text-secondary);">Processing...</div>
                </div>
            </div>
            <span class="badge badge-warning" id="badge-${id}">Processing</span>
        </div>
    `;
    list.insertAdjacentHTML('afterbegin', itemHTML);

    // Simulate backend processing
    setTimeout(() => {
        const badge = document.getElementById(`badge-${id}`);
        const info = document.querySelector(`#mat-${id} .material-info div:nth-child(2)`);
        if (badge && info) {
            badge.className = 'badge badge-success';
            badge.innerText = 'Processed';
            info.innerText = 'AI extracted successfully';
            showToast('Document processed successfully!', 'success');
        }
    }, 3000);
}

/* =========================================================
   Review Logic (teacher/review.html)
   ========================================================= */

function approveAnswer(id) {
    const card = document.getElementById(`review-${id}`);
    const statusBadge = document.getElementById(`status-${id}`);
    if (card && statusBadge) {
        card.className = 'card review-card approved';
        statusBadge.className = 'badge badge-success';
        statusBadge.innerText = 'Approved';
        showToast('Answer approved for students.', 'success');
        removeActionButtons(id);
    }
}

function rejectAnswer(id) {
    const card = document.getElementById(`review-${id}`);
    const statusBadge = document.getElementById(`status-${id}`);
    if (card && statusBadge) {
        card.className = 'card review-card rejected';
        statusBadge.className = 'badge badge-danger';
        statusBadge.innerText = 'Rejected';
        showToast('Answer rejected.', 'error');
        removeActionButtons(id);
    }
}

function toggleEditAnswer(id) {
    const answerDiv = document.getElementById(`answer-text-${id}`);
    const btn = document.getElementById(`edit-btn-${id}`);
    
    if (answerDiv.querySelector('textarea')) {
        // Save logic
        const newText = answerDiv.querySelector('textarea').value;
        answerDiv.innerHTML = newText.replace(/\n/g, '<br>');
        btn.innerText = 'Edit Answer';
        showToast('Answer updated manually.', 'success');
    } else {
        // Edit logic
        const currentText = answerDiv.innerHTML.replace(/<br>/g, '\n');
        answerDiv.innerHTML = `<textarea>${currentText}</textarea>`;
        btn.innerText = 'Save Changes';
    }
}

function removeActionButtons(id) {
    const actions = document.getElementById(`actions-${id}`);
    if (actions) {
        actions.style.display = 'none';
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // If on course builder
    if (document.getElementById('units-container')) {
        addUnit();
    }
    
    // If on materials page
    if (document.getElementById('upload-zone')) {
        setupFileUpload();
    }
});
