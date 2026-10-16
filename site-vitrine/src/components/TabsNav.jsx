import { useState } from 'react';

const tabs = [
  {
    id: 'assets',
    label: '1. Parc & Assets',
    tag: 'Matériel & Postes',
    description:
      'Supervision du matériel physique, cycle de vie des postes, serveurs et suivi des dates de fin de garantie.',
    strengths: {
      Grafana: 'Alerte temps réel sur pannes et états hardware via télémétrie.',
      Metabase: 'Exploration ad-hoc et inventaires filtrés par pôle pour les gestionnaires.',
      'Power BI': 'Agrégations multidimensionnelles historiques et analyses d’amortissement.',
    },
  },
  {
    id: 'licenses',
    label: '2. Licences & Coûts',
    tag: 'FinOps & Abonnements',
    description:
      'Gouvernance des dépenses logicielles, suivi des licences attribuées vs inactives et détection des surcoûts.',
    strengths: {
      Grafana: 'Tableau de bord synthétique du coût mensuel global et seuils de consommation.',
      Metabase: 'Questions no-code pour identifier rapidement les comptes sans activité.',
      'Power BI': 'Croisement comptable avec les centres de coûts et projection budgétaire.',
    },
  },
  {
    id: 'monitoring',
    label: '3. Supervision SI',
    tag: 'Santé & Disponibilité',
    description:
      'Surveillance proactive de la disponibilité des services, latence réseau et respect des SLO/SLA.',
    strengths: {
      Grafana: 'Performance maximale sur les métriques temporelles et alertes Slack/PagerDuty.',
      Metabase: 'Rapports d’incidents périodiques et tableaux de bord pour la direction.',
      'Power BI': 'Rapports trimestriels de gouvernance et conformité contractuelle.',
    },
  },
];

export default function TabsNav() {
  const [activeTab, setActiveTab] = useState(0);
  const current = tabs[activeTab];

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm space-y-4">
      {/* Tab buttons */}
      <div className="flex flex-wrap gap-2 border-b border-gray-200 pb-3">
        {tabs.map((tab, idx) => {
          const isActive = idx === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(idx)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                isActive
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  isActive ? 'bg-blue-700 text-blue-100' : 'bg-gray-200 text-gray-600'
                }`}
              >
                {tab.tag}
              </span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="space-y-3">
        <p className="text-gray-700 text-sm leading-relaxed">{current.description}</p>
        <div className="grid md:grid-cols-3 gap-3 pt-1">
          {Object.entries(current.strengths).map(([tool, text]) => (
            <div key={tool} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
              <span className="font-semibold text-gray-900 block mb-1">{tool}</span>
              <span className="text-gray-600">{text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
