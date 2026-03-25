(function() {
  const { useState, useEffect } = React;

  const ReportsApp = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [reports, setReports] = useState(() => {
      const saved = localStorage.getItem('user_reports');
      return saved ? JSON.parse(saved) : [];
    });
    const [viewingReport, setViewingReport] = useState(null);
    const [form, setForm] = useState({ title: '', doctor: '', date: '', type: 'Blood Test', file: null });

    useEffect(() => {
      localStorage.setItem('user_reports', JSON.stringify(reports));
    }, [reports]);

    useEffect(() => {
      if (window.location.hash === '#reports') setIsOpen(true);
    }, []);

    window.toggleReports = (val) => setIsOpen(val);

    const handleFileChange = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onloadend = () => setForm({ ...form, file: reader.result });
        reader.readAsDataURL(file);
      }
    };

    const addReport = (e) => {
      e.preventDefault();
      if (!form.file) return alert("Please upload a file");
      const newReport = { ...form, id: Date.now(), createdAt: new Date().toISOString() };
      setReports([newReport, ...reports]);
      setForm({ title: '', doctor: '', date: '', type: 'Blood Test', file: null });
    };

    const deleteReport = (id) => {
      if (confirm("Are you sure?")) setReports(reports.filter(r => r.id !== id));
    };

    const downloadReport = (report) => {
      const link = document.createElement('a');
      link.href = report.file;
      link.download = `Report_${report.title.replace(/\s+/g, '_')}_${report.date}.png`;
      link.click();
    };

    if (!isOpen) return null;

    return (
      <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'var(--bg)', zIndex: 1000, overflowY: 'auto', padding: '20px', boxSizing: 'border-box' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
            <h2>🧾 Medical Reports Storage</h2>
            <button className="btn" style={{ background: 'var(--text)', color: 'var(--bg)', width: 'auto' }} onClick={() => setIsOpen(false)}>Close Dash</button>
          </div>
          <div className="card" style={{ marginBottom: '30px' }}>
            <h3>Upload New Report</h3>
            <form onSubmit={addReport} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
              <input type="text" placeholder="Title" required value={form.title} onChange={e => setForm({...form, title: e.target.value})} />
              <input type="text" placeholder="Doctor" required value={form.doctor} onChange={e => setForm({...form, doctor: e.target.value})} />
              <input type="date" required value={form.date} onChange={e => setForm({...form, date: e.target.value})} />
              <select style={{ padding: '10px', borderRadius: '10px', border: '1px solid #ccc' }} value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                <option>Blood Test</option><option>X-Ray</option><option>MRI / CT Scan</option><option>Prescription</option><option>General Checkup</option>
              </select>
              <input type="file" accept="image/*,application/pdf" required onChange={handleFileChange} />
              <button type="submit" className="btn" style={{ gridColumn: '1 / -1' }}>Save Report</button>
            </form>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {reports.map(report => (
              <div key={report.id} className="card" style={{ border: '1px solid #eee' }}>
                <h4>{report.title}</h4>
                <p>📅 {report.date} | 👨‍⚕️ {report.doctor}</p>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button className="btn" onClick={() => setViewingReport(report)}>View</button>
                  <button className="btn" style={{ background: '#f87171' }} onClick={() => deleteReport(report.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
        {viewingReport && (
          <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0,0,0,0.8)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setViewingReport(null)}>
            <div style={{ position: 'relative' }} onClick={e => e.stopPropagation()}>
              <button style={{ position: 'absolute', top: -30, right: 0, color: 'white' }} onClick={() => setViewingReport(null)}>✕</button>
              <img src={viewingReport.file} style={{ maxWidth: '90vw', maxHeight: '90vh' }} />
            </div>
          </div>
        )}
      </div>
    );
  };

  const reportsRoot = ReactDOM.createRoot(document.getElementById('reports-root'));
  reportsRoot.render(<ReportsApp />);
})();
