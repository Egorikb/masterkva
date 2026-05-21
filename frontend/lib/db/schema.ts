// SQLite Database Schema for DeepTutor
// Simple file-based storage using JSON

export interface StudentProfile {
  id: string;
  name: string;
  grade: number;
  diagnosticGrade: number;
  currentTopic: string;
  beltLevel: string;
  createdAt: string;
  lastVisit: string;
}

export interface SessionProgress {
  id: string;
  studentId: string;
  strongTopics: string[];
  weakSpots: string[];
  correctCount: number;
  errorCount: number;
  sessionGoal: string;
  timestamp: string;
}

const DB_FILE = '/tmp/deeptutor_db.json';

export const db = {
  // Load database
  load: (): { profiles: StudentProfile[]; sessions: SessionProgress[] } => {
    try {
      const fs = require('fs');
      if (fs.existsSync(DB_FILE)) {
        return JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
      }
    } catch (e) {}
    return { profiles: [], sessions: [] };
  },
  
  // Save database
  save: (data: { profiles: StudentProfile[]; sessions: SessionProgress[] }) => {
    const fs = require('fs');
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
  },
  
  // Save profile
  saveProfile: (profile: StudentProfile) => {
    const data = db.load();
    const idx = data.profiles.findIndex(p => p.id === profile.id);
    if (idx >= 0) {
      data.profiles[idx] = profile;
    } else {
      data.profiles.push(profile);
    }
    db.save(data);
  },
  
  // Get profile
  getProfile: (name: string): StudentProfile | null => {
    const data = db.load();
    return data.profiles.find(p => p.name === name) || null;
  },
  
  // Save session
  saveSession: (session: SessionProgress) => {
    const data = db.load();
    data.sessions.push(session);
    db.save(data);
  },
  
  // Get sessions
  getSessions: (studentId: string): SessionProgress[] => {
    const data = db.load();
    return data.sessions.filter(s => s.studentId === studentId);
  }
};

export default db;
