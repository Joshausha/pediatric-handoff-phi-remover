/**
 * Pediatric Handoff PHI Remover - Frontend Application
 *
 * Handles:
 * - Audio recording via MediaRecorder API
 * - File upload
 * - API communication
 * - Results display
 */

class HandoffTranscriber {
    constructor() {
        // State
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioBlob = null;
        this.isRecording = false;
        this.recordingStartTime = null;
        this.timerInterval = null;

        // DOM elements
        this.recordBtn = document.getElementById('record-btn');
        this.recordingTimer = document.getElementById('recording-timer');
        this.audioPreview = document.getElementById('audio-preview');
        this.audioPlayer = document.getElementById('audio-player');
        this.processBtn = document.getElementById('process-btn');
        this.discardBtn = document.getElementById('discard-btn');
        this.uploadBtn = document.getElementById('upload-btn');
        this.fileInput = document.getElementById('file-input');
        this.fileName = document.getElementById('file-name');
        this.processingPanel = document.getElementById('processing-panel');
        this.resultsPanel = document.getElementById('results-panel');
        this.statusIndicator = document.getElementById('status-indicator');

        // Processing steps
        this.stepTranscribe = document.getElementById('step-transcribe');
        this.stepDeidentify = document.getElementById('step-deidentify');

        // Results elements
        this.phiTotal = document.getElementById('phi-total');
        this.phiBreakdown = document.getElementById('phi-breakdown');
        this.cleanTranscript = document.getElementById('clean-transcript');
        this.entitiesList = document.getElementById('entities-list');
        this.warnings = document.getElementById('warnings');
        this.copyBtn = document.getElementById('copy-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.newBtn = document.getElementById('new-btn');

        this.init();
    }

    async init() {
        // Check backend health
        await this.checkHealth();

        // Set up event listeners
        this.recordBtn.addEventListener('click', () => this.toggleRecording());
        this.processBtn.addEventListener('click', () => this.processAudio());
        this.discardBtn.addEventListener('click', () => this.discardRecording());
        this.uploadBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.copyBtn.addEventListener('click', () => this.copyToClipboard());
        this.downloadBtn.addEventListener('click', () => this.downloadTranscript());
        this.newBtn.addEventListener('click', () => this.reset());
    }

    async checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();

            if (data.status === 'healthy') {
                this.statusIndicator.textContent = 'Ready';
                this.statusIndicator.className = 'status-badge status-ready';
                this.recordBtn.disabled = false;
            } else {
                throw new Error('Backend unhealthy');
            }
        } catch (error) {
            this.statusIndicator.textContent = 'Offline';
            this.statusIndicator.className = 'status-badge status-error';
            console.error('Health check failed:', error);
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Determine supported MIME type
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : 'audio/webm';

            this.mediaRecorder = new MediaRecorder(stream, { mimeType });
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.audioBlob = new Blob(this.audioChunks, { type: mimeType });
                this.showAudioPreview();

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start(1000); // Collect data every second
            this.isRecording = true;
            this.recordingStartTime = Date.now();

            // Update UI
            this.recordBtn.classList.add('recording');
            this.recordingTimer.classList.remove('hidden');
            this.startTimer();

            // Hide any previous results
            this.audioPreview.classList.add('hidden');
            this.resultsPanel.classList.add('hidden');

        } catch (error) {
            console.error('Failed to start recording:', error);
            alert('Could not access microphone. Please ensure microphone permissions are granted.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.stopTimer();

            // Update UI
            this.recordBtn.classList.remove('recording');
        }
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            this.recordingTimer.textContent =
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    showAudioPreview() {
        const url = URL.createObjectURL(this.audioBlob);
        this.audioPlayer.src = url;
        this.audioPreview.classList.remove('hidden');
    }

    discardRecording() {
        this.audioBlob = null;
        this.audioChunks = [];
        this.audioPreview.classList.add('hidden');
        this.recordingTimer.classList.add('hidden');
        this.recordingTimer.textContent = '00:00';
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.audioBlob = file;
            this.fileName.textContent = file.name;
            this.showAudioPreview();
        }
    }

    async processAudio() {
        if (!this.audioBlob) {
            alert('No audio to process');
            return;
        }

        // Show processing panel
        this.audioPreview.classList.add('hidden');
        this.processingPanel.classList.remove('hidden');
        this.resultsPanel.classList.add('hidden');

        // Reset step indicators
        this.setStepStatus('step-transcribe', 'pending');
        this.setStepStatus('step-deidentify', 'pending');

        try {
            // Step 1: Transcribing
            this.setStepStatus('step-transcribe', 'active');

            const formData = new FormData();
            formData.append('file', this.audioBlob, 'recording.webm');

            // Get selected transfer mode (Phase 23)
            const transferModeInput = document.querySelector('input[name="transfer-mode"]:checked');
            const transferMode = transferModeInput ? transferModeInput.value : 'conservative';
            formData.append('transfer_mode', transferMode);

            // Use AbortController with 30-minute timeout for long recordings
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30 * 60 * 1000);

            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Processing failed');
            }

            this.setStepStatus('step-transcribe', 'complete');
            this.setStepStatus('step-deidentify', 'active');

            const result = await response.json();

            // Small delay to show deidentify step
            await new Promise(resolve => setTimeout(resolve, 500));
            this.setStepStatus('step-deidentify', 'complete');

            // Show results
            this.displayResults(result);

        } catch (error) {
            console.error('Processing error:', error);
            alert(`Processing failed: ${error.message}`);
            this.processingPanel.classList.add('hidden');
            this.audioPreview.classList.remove('hidden');
        }
    }

    setStepStatus(stepId, status) {
        const step = document.getElementById(stepId);
        const icon = step.querySelector('.step-icon');
        icon.className = `step-icon ${status}`;
    }

    displayResults(result) {
        // Hide processing, show results
        this.processingPanel.classList.add('hidden');
        this.resultsPanel.classList.remove('hidden');

        // Phase 23: Use new phi_detected structure for accurate removed count
        const phiData = result.phi_detected || result.phi_removed; // Fallback for compatibility

        // PHI summary - show removed count (not total detected)
        this.phiTotal.textContent = phiData.removed_count !== undefined
            ? phiData.removed_count
            : phiData.total_count;

        // Update label based on whether entities were preserved
        const phiLabel = document.querySelector('.phi-label');
        if (phiData.preserved_count > 0) {
            phiLabel.textContent = 'PHI elements removed';
            phiLabel.title = `${phiData.preserved_count} location(s) preserved for clinical mode`;
        } else {
            phiLabel.textContent = 'PHI elements removed';
            phiLabel.title = '';
        }

        // Breakdown by type - show removed entities first, then preserved
        this.phiBreakdown.innerHTML = '';

        // Removed entities (redacted)
        if (phiData.removed_by_type) {
            for (const [type, count] of Object.entries(phiData.removed_by_type)) {
                const tag = document.createElement('span');
                tag.className = 'phi-tag phi-tag-removed';
                tag.innerHTML = `
                    <span class="phi-tag-count">${count}</span>
                    ${this.formatEntityType(type)} (removed)
                `;
                this.phiBreakdown.appendChild(tag);
            }
        }

        // Preserved entities (clinical mode)
        if (phiData.preserved_by_type) {
            for (const [type, count] of Object.entries(phiData.preserved_by_type)) {
                const tag = document.createElement('span');
                tag.className = 'phi-tag phi-tag-preserved';
                tag.innerHTML = `
                    <span class="phi-tag-count">${count}</span>
                    ${this.formatEntityType(type)} (preserved)
                `;
                this.phiBreakdown.appendChild(tag);
            }
        }

        // Fallback to legacy format if new structure not available
        if (!phiData.removed_by_type && !phiData.preserved_by_type && phiData.by_type) {
            for (const [type, count] of Object.entries(phiData.by_type)) {
                const tag = document.createElement('span');
                tag.className = 'phi-tag';
                tag.innerHTML = `
                    <span class="phi-tag-count">${count}</span>
                    ${this.formatEntityType(type)}
                `;
                this.phiBreakdown.appendChild(tag);
            }
        }

        // Clean transcript
        this.cleanTranscript.textContent = result.clean_transcript || '(No speech detected)';

        // Entities list
        this.entitiesList.innerHTML = '';
        for (const entity of result.entities) {
            const item = document.createElement('div');
            item.className = 'entity-item';
            item.innerHTML = `
                <span class="entity-type">${this.formatEntityType(entity.type)}</span>
                <span class="entity-preview">${entity.text_preview}</span>
                <span class="entity-score">${(entity.score * 100).toFixed(0)}%</span>
            `;
            this.entitiesList.appendChild(item);
        }

        // Warnings
        if (result.warnings && result.warnings.length > 0) {
            this.warnings.innerHTML = result.warnings.map(w => `<p>${w}</p>`).join('');
            this.warnings.classList.remove('hidden');
        } else {
            this.warnings.classList.add('hidden');
        }

        // Store for copy/download
        this._lastResult = result;
    }

    formatEntityType(type) {
        const typeMap = {
            'PERSON': 'Name',
            'GUARDIAN_NAME': 'Guardian',
            'PHONE_NUMBER': 'Phone',
            'EMAIL_ADDRESS': 'Email',
            'DATE_TIME': 'Date',
            'LOCATION': 'Location',
            'MEDICAL_RECORD_NUMBER': 'MRN',
            'ROOM': 'Room',
            'PEDIATRIC_AGE': 'Age',
        };
        return typeMap[type] || type.replace(/_/g, ' ').toLowerCase();
    }

    async copyToClipboard() {
        if (!this._lastResult) return;

        try {
            await navigator.clipboard.writeText(this._lastResult.clean_transcript);

            // Visual feedback
            const originalText = this.copyBtn.textContent;
            this.copyBtn.textContent = 'Copied!';
            setTimeout(() => {
                this.copyBtn.textContent = originalText;
            }, 2000);

        } catch (error) {
            console.error('Copy failed:', error);
            alert('Failed to copy to clipboard');
        }
    }

    downloadTranscript() {
        if (!this._lastResult) return;

        const text = this._lastResult.clean_transcript;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `handoff_transcript_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    reset() {
        this.audioBlob = null;
        this.audioChunks = [];
        this._lastResult = null;

        this.audioPreview.classList.add('hidden');
        this.processingPanel.classList.add('hidden');
        this.resultsPanel.classList.add('hidden');
        this.recordingTimer.classList.add('hidden');
        this.recordingTimer.textContent = '00:00';
        this.fileName.textContent = '';
        this.fileInput.value = '';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.app = new HandoffTranscriber();
});
