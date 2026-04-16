interface PendingApprovalProps {
  email: string;
  status: 'pending' | 'blocked';
  onSignOut: () => void;
}

export function PendingApproval({ email, status, onSignOut }: PendingApprovalProps) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: '#f5f5f5',
    }}>
      <div style={{
        background: 'white',
        padding: '40px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '440px',
        textAlign: 'center',
      }}>
        <h1 style={{ marginBottom: '10px' }}>Artemis</h1>

        {status === 'pending' ? (
          <>
            <h2 style={{ color: '#666', fontWeight: 400, fontSize: '18px', marginBottom: '20px' }}>
              Account Pending Approval
            </h2>
            <p style={{ color: '#888', lineHeight: 1.6 }}>
              Your account <strong>{email}</strong> has been created
              but requires admin approval before you can access the dashboard.
            </p>
            <p style={{ color: '#888', lineHeight: 1.6, marginTop: '10px' }}>
              Please contact the administrator and check back later.
            </p>
          </>
        ) : (
          <>
            <h2 style={{ color: '#d32f2f', fontWeight: 400, fontSize: '18px', marginBottom: '20px' }}>
              Account Blocked
            </h2>
            <p style={{ color: '#888', lineHeight: 1.6 }}>
              Your account <strong>{email}</strong> has been blocked.
              Contact the administrator for details.
            </p>
          </>
        )}

        <button
          onClick={onSignOut}
          style={{
            marginTop: '30px',
            padding: '10px 24px',
            background: '#eee',
            border: 'none',
            borderRadius: '4px',
            fontSize: '14px',
            cursor: 'pointer',
          }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
