import { useEffect, useState } from "react";
import { Building2, Target, Zap, Edit2 } from "lucide-react";

interface UserProfile {
  id: number;
  company_name: string | null;
  offerings: string[];
  target_markets: string[];
  strengths: string[];
}

export function UserProfilePanel() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/profile")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setProfile(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-4 text-gray-500 text-sm">Lade Profil...</div>
    );
  }

  if (!profile || !profile.company_name) {
    return (
      <div className="p-4">
        <p className="text-gray-500 text-sm">
          Noch kein Profil angelegt. Erzaehle dem Assistenten in einer Konversation ueber dein Unternehmen.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Building2 size={18} className="text-blue-400" />
        <h3 className="font-bold text-white">{profile.company_name}</h3>
      </div>

      {profile.offerings.length > 0 && (
        <div>
          <div className="flex items-center gap-1 text-xs font-medium text-gray-400 mb-1">
            <Zap size={12} /> Angebote
          </div>
          <div className="flex flex-wrap gap-1">
            {profile.offerings.map((o, i) => (
              <span key={i} className="px-2 py-0.5 bg-green-600/20 text-green-300 rounded-full text-xs">
                {o}
              </span>
            ))}
          </div>
        </div>
      )}

      {profile.target_markets.length > 0 && (
        <div>
          <div className="flex items-center gap-1 text-xs font-medium text-gray-400 mb-1">
            <Target size={12} /> Zielmaerkte
          </div>
          <div className="flex flex-wrap gap-1">
            {profile.target_markets.map((m, i) => (
              <span key={i} className="px-2 py-0.5 bg-purple-600/20 text-purple-300 rounded-full text-xs">
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {profile.strengths.length > 0 && (
        <div>
          <div className="flex items-center gap-1 text-xs font-medium text-gray-400 mb-1">
            <Zap size={12} /> Staerken
          </div>
          <div className="flex flex-wrap gap-1">
            {profile.strengths.map((s, i) => (
              <span key={i} className="px-2 py-0.5 bg-yellow-600/20 text-yellow-300 rounded-full text-xs">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
