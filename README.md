# Shiksha Sahayak 🎓

### AI-Powered Syllabus-Based Learning Assistant

Shiksha Sahayak is an AI-powered learning assistant designed to bridge the gap between **general-purpose AI and syllabus-specific, examination-oriented learning**.

Instead of making students repeatedly provide context and write detailed prompts, Shiksha Sahayak creates a **teacher-controlled academic environment** where approved study material becomes the foundation for AI-assisted learning.

Students can learn concepts at their preferred level and language, generate answers according to the required marks, and identify topics that need more revision.

---

## 🚀 Problem

General-purpose AI tools are powerful at explaining concepts, but they are not specifically designed around a student's:

* 📚 Teacher-approved study material
* 📝 Specific syllabus and topics
* 🎯 Examination requirements
* 📊 Learning level
* 🌐 Preferred language
* 🔑 Important technical terminology
* 📈 Individual learning gaps

This creates a gap between **understanding a concept with AI** and **preparing effectively according to what a course actually requires**.

---

## 💡 Our Solution

Shiksha Sahayak puts AI inside a structured, teacher-controlled learning environment.

### For Teachers

* Create and manage courses
* Define syllabus and topics
* Upload approved study material
* Review AI-generated content
* Maintain control over the academic knowledge base

### For Students

* Select a topic to study
* Choose a learning level:

  * Basic
  * Intermediate
  * Advanced
* Choose English or Hindi
* Generate answers for:

  * 2 marks
  * 5 marks
  * 10 marks
* Switch between:

  * **Learn Simply** — for concept understanding
  * **Exam Answer** — for examination-oriented preparation
* Practice MCQs
* Identify weak topics and areas requiring revision

---

## 🔄 How It Works

```text
Teacher
   ↓
Course & Syllabus
   ↓
Approved Study Material
   ↓
Content Extraction & Processing
   ↓
Course Knowledge Base
   ↓
Student selects Topic + Level + Language + Marks
   ↓
Relevant Content Retrieved using RAG
   ↓
Gemini AI Processing
   ↓
Keyword & Source Verification
   ↓
Teacher Approval
   ↓
Final Learning / Exam Response
   ↓
MCQ Assessment
   ↓
Identify Weak Topics
   ↓
Targeted Revision
```

The goal is to create a continuous learning loop:

**Learn → Practice → Assess → Identify Gaps → Revise**

---

## 🧠 Key Features

### 📚 Teacher-Verified Learning

Students learn from content uploaded and approved by their teachers rather than relying solely on unrestricted AI-generated information.

### 🎯 Mark-Based Answer Generation

Generate structured answers according to the required marks, such as 2, 5, or 10 marks.

### 📖 Learn Simply

Difficult academic concepts can be explained according to the student's selected learning level.

### 📝 Exam Answer Mode

Provides examination-oriented responses while preserving important technical terminology.

### 🌐 English & Hindi Support

Supports learning and answer generation in English and Hindi.

### 🔍 Source & Keyword Verification

Checks generated responses against the retrieved academic content and important technical terms.

### 📊 MCQ-Based Gap Analysis

MCQ performance can be analyzed to identify topics where a student needs additional revision.

### 👨‍🏫 Teacher Approval

Teachers remain involved in validating academic content and maintaining control over the learning material.

---

## ⚙️ Technology Stack

| Component           | Technology                           |
| ------------------- | ------------------------------------ |
| Frontend            | HTML, CSS, JavaScript                |
| Backend             | Python, Flask                        |
| AI                  | Gemini API                           |
| Retrieval           | RAG (Retrieval-Augmented Generation) |
| Document Processing | PyMuPDF                              |
| Visual Processing   | YOLOv8                               |
| Database            | SQLite / Firebase                    |
| Output Generation   | python-pptx                          |

---

## 🏗️ System Architecture

Shiksha Sahayak follows a layered architecture:

**Input Layer**

* Teacher-uploaded PDFs
* Supported academic images
* Student requirements

↓

**Processing Layer**

* Text and visual content extraction
* Content organization
* Relevant information retrieval

↓

**AI Layer**

* Gemini API
* RAG-based contextual generation
* Explanation and answer generation
* Translation
* MCQ generation

↓

**Verification Layer**

* Source checking
* Keyword checking
* Teacher review

↓

**Assessment Layer**

* MCQ performance analysis
* Weak-topic identification
* Targeted revision

---

## 🛡️ Reliability & Safety

AI-generated educational content can sometimes contain incorrect or unsupported information.

Shiksha Sahayak addresses this through:

* **Source grounding** using approved study material
* **Keyword verification** for important technical terminology
* **Teacher review and approval**
* **Image-quality warnings** for unclear visual inputs

The objective is not to eliminate every possible AI error, but to create a more controlled and verifiable academic workflow.

---

## 📈 Future Scope

Shiksha Sahayak can be extended beyond the initial MVP through:

* Support for additional subjects and courses
* More Indian and international languages
* Deployment across multiple educational institutions
* More personalized revision recommendations
* Improved academic image and diagram processing
* Domain-specific YOLOv8 training using labelled academic datasets
* Deeper analysis of student learning patterns and performance

The long-term vision is to evolve from a syllabus-based AI assistant into a **complete personalized academic learning platform**.

---

## 🎯 Target Users

* 👨‍🎓 Students
* 👩‍🏫 Teachers
* 🏫 Educational Institutions

---

## 🌟 Vision

> **Learn at your level. Write with confidence.**

Shiksha Sahayak is built around a simple idea:

**AI should not only be able to answer a student's question — it should understand what that student is actually supposed to learn.**

---

## 👥 Team

### NextGen Developers

Built for **Smart India Hackathon 2026**

**Problem Statement:** SE-02
**Theme:** Smart Education
**Problem Statement:** AI Powered Syllabus-Based Learning Assistant

---

## 📌 Project Status

🚧 **Currently under development**

This project is being developed as part of **Smart India Hackathon 2026**.

---

## 📄 License

This project is currently intended for educational and hackathon purposes.

