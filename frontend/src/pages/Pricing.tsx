export function PricingPage() {
  const plans = [
    {
      name: 'Trial', price: 'Free', period: '14 days', color: 'text-primary-400', popular: false,
      features: ['DuckDuckGo search', 'HIBP basic check', 'Dark web gateways', 'Privacy scoring', 'Self-hosted'],
    },
    {
      name: 'Professional', price: '$299', period: 'one-time', color: 'text-accent-400', popular: true,
      features: ['Everything in Trial', 'Bring Your Own API Keys', 'SerpAPI / Google CSE', 'Dehashed + IntelX', 'Twitter scanning', 'Email support', '1 year updates'],
    },
    {
      name: 'Enterprise', price: '$999', period: 'one-time', color: 'text-purple-400', popular: false,
      features: ['Everything in Pro', 'Unlimited users', 'White-label', 'Multi-tenant', 'API access', 'Dedicated support', 'Lifetime updates'],
    },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-slide-up px-4">
      <div className="text-center">
        <h2 className="text-2xl sm:text-3xl font-bold font-heading gradient-text mb-3">Choose your plan</h2>
        <p className="text-sm text-gray-500 font-mono">One-time payment. Lifetime access. No subscriptions.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {plans.map(p => (
          <div key={p.name} className={`glass-card relative text-center ${p.popular ? 'border-primary-500/20 bg-primary-500/[0.02]' : ''}`}>
            {p.popular && (
              <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-primary-500 text-white
                               text-[10px] font-bold font-heading rounded-full uppercase tracking-wider">
                Best Value
              </span>
            )}
            <h3 className={`text-lg font-heading font-bold ${p.color} mb-1`}>{p.name}</h3>
            <div className="text-3xl font-bold font-heading text-gray-100 mt-3 mb-0.5">{p.price}</div>
            <div className="text-[11px] text-gray-600 font-mono mb-4">{p.period}</div>
            <ul className="space-y-2 mb-5 text-left">
              {p.features.map(f => (
                <li key={f} className="text-[12px] text-gray-400 font-mono flex items-start gap-2">
                  <span className="text-success-400 mt-0.5 flex-shrink-0">&#x2713;</span>
                  {f}
                </li>
              ))}
            </ul>
            <button className={`w-full btn-primary text-xs ${p.popular ? '' : '!bg-white/5 !text-gray-300 hover:!bg-white/10'}`}>
              {p.name === 'Enterprise' ? 'Contact Sales' : p.name === 'Trial' ? 'Start Free Trial' : 'Buy Now'}
            </button>
          </div>
        ))}
      </div>

      <div className="text-center">
        <p className="text-[11px] text-gray-600 font-mono">
          Need a custom plan? <span className="text-primary-400 cursor-pointer hover:underline">Contact us</span>
        </p>
      </div>
    </div>
  )
}
