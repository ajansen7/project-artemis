import { useAdmin } from '../hooks/useAdmin';
import type { UserProfile } from '../types';

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, { bg: string; fg: string }> = {
    approved: { bg: '#e8f5e9', fg: '#2e7d32' },
    pending:  { bg: '#fff3e0', fg: '#e65100' },
    blocked:  { bg: '#ffebee', fg: '#c62828' },
  };
  const c = colors[status] || { bg: '#eee', fg: '#666' };
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      fontWeight: 600,
      background: c.bg,
      color: c.fg,
    }}>
      {status}
    </span>
  );
}

function RoleBadge({ role }: { role: string }) {
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      fontWeight: 600,
      background: role === 'admin' ? '#e3f2fd' : '#f5f5f5',
      color: role === 'admin' ? '#1565c0' : '#666',
    }}>
      {role}
    </span>
  );
}

function UserRow({ user, onApprove, onBlock, onSetRole }: {
  user: UserProfile;
  onApprove: () => void;
  onBlock: () => void;
  onSetRole: (role: 'admin' | 'user') => void;
}) {
  return (
    <tr>
      <td style={{ padding: '10px 12px' }}>{user.email}</td>
      <td style={{ padding: '10px 12px' }}><RoleBadge role={user.role} /></td>
      <td style={{ padding: '10px 12px' }}><StatusBadge status={user.status} /></td>
      <td style={{ padding: '10px 12px', fontSize: '13px', color: '#888' }}>
        {new Date(user.created_at).toLocaleDateString()}
      </td>
      <td style={{ padding: '10px 12px' }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          {user.status === 'pending' && (
            <button onClick={onApprove} style={actionBtn('#2e7d32')}>Approve</button>
          )}
          {user.status === 'approved' && (
            <button onClick={onBlock} style={actionBtn('#c62828')}>Block</button>
          )}
          {user.status === 'blocked' && (
            <button onClick={onApprove} style={actionBtn('#2e7d32')}>Unblock</button>
          )}
          {user.role === 'user' && user.status === 'approved' && (
            <button onClick={() => onSetRole('admin')} style={actionBtn('#1565c0')}>Make Admin</button>
          )}
          {user.role === 'admin' && (
            <button onClick={() => onSetRole('user')} style={actionBtn('#666')}>Remove Admin</button>
          )}
        </div>
      </td>
    </tr>
  );
}

function actionBtn(color: string): React.CSSProperties {
  return {
    padding: '4px 10px',
    fontSize: '12px',
    border: `1px solid ${color}`,
    borderRadius: '4px',
    background: 'white',
    color,
    cursor: 'pointer',
  };
}

export function AdminPanel() {
  const { users, loading, error, approveUser, blockUser, setRole } = useAdmin();

  const pending = users.filter(u => u.status === 'pending');
  const others = users.filter(u => u.status !== 'pending');

  if (loading) return <div style={{ padding: '20px' }}>Loading users...</div>;
  if (error) return <div style={{ padding: '20px', color: '#d32f2f' }}>{error}</div>;

  return (
    <div style={{ padding: '0 4px' }}>
      {pending.length > 0 && (
        <div style={{
          background: '#fff3e0',
          border: '1px solid #ffe0b2',
          borderRadius: '6px',
          padding: '12px 16px',
          marginBottom: '16px',
          fontSize: '14px',
          color: '#e65100',
        }}>
          <strong>{pending.length}</strong> user{pending.length > 1 ? 's' : ''} awaiting approval
        </div>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
            <th style={{ padding: '10px 12px', fontWeight: 600 }}>Email</th>
            <th style={{ padding: '10px 12px', fontWeight: 600 }}>Role</th>
            <th style={{ padding: '10px 12px', fontWeight: 600 }}>Status</th>
            <th style={{ padding: '10px 12px', fontWeight: 600 }}>Joined</th>
            <th style={{ padding: '10px 12px', fontWeight: 600 }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {[...pending, ...others].map((user) => (
            <UserRow
              key={user.user_id}
              user={user}
              onApprove={() => approveUser(user.user_id)}
              onBlock={() => blockUser(user.user_id)}
              onSetRole={(role) => setRole(user.user_id, role)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
