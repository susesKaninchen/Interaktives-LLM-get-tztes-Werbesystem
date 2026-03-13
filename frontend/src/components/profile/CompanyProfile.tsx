import { Building2, Globe, MapPin, Phone, Mail, Star, Users } from "lucide-react";

interface CompanyProfileProps {
  profile: {
    name: string;
    website?: string;
    address?: string;
    phone?: string;
    email?: string;
    services?: string[];
    team?: string[];
    description?: string;
    usp?: string;
  };
}

export function CompanyProfileCard({ profile }: CompanyProfileProps) {
  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Building2 size={20} className="text-blue-400" />
        <h3 className="font-bold text-white text-lg">{profile.name}</h3>
      </div>

      <div className="grid grid-cols-1 gap-2 text-sm">
        {profile.website && (
          <div className="flex items-center gap-2 text-gray-300">
            <Globe size={14} className="text-gray-500 shrink-0" />
            <a href={profile.website} target="_blank" rel="noopener noreferrer"
              className="text-blue-400 hover:underline truncate">
              {profile.website}
            </a>
          </div>
        )}
        {profile.address && (
          <div className="flex items-center gap-2 text-gray-300">
            <MapPin size={14} className="text-gray-500 shrink-0" />
            <span>{profile.address}</span>
          </div>
        )}
        {profile.phone && (
          <div className="flex items-center gap-2 text-gray-300">
            <Phone size={14} className="text-gray-500 shrink-0" />
            <span>{profile.phone}</span>
          </div>
        )}
        {profile.email && (
          <div className="flex items-center gap-2 text-gray-300">
            <Mail size={14} className="text-gray-500 shrink-0" />
            <span>{profile.email}</span>
          </div>
        )}
      </div>

      {profile.description && (
        <p className="text-sm text-gray-300">{profile.description}</p>
      )}

      {profile.services && profile.services.length > 0 && (
        <div>
          <div className="flex items-center gap-1 text-xs font-medium text-gray-400 mb-1">
            <Star size={12} /> Leistungen
          </div>
          <div className="flex flex-wrap gap-1">
            {profile.services.map((s, i) => (
              <span key={i} className="px-2 py-0.5 bg-blue-600/20 text-blue-300 rounded-full text-xs">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {profile.team && profile.team.length > 0 && (
        <div>
          <div className="flex items-center gap-1 text-xs font-medium text-gray-400 mb-1">
            <Users size={12} /> Team
          </div>
          <div className="flex flex-wrap gap-1">
            {profile.team.map((t, i) => (
              <span key={i} className="px-2 py-0.5 bg-gray-700 text-gray-300 rounded-full text-xs">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {profile.usp && (
        <div className="p-2 bg-blue-600/10 border border-blue-600/20 rounded-lg">
          <p className="text-xs text-blue-300"><strong>USP:</strong> {profile.usp}</p>
        </div>
      )}
    </div>
  );
}
