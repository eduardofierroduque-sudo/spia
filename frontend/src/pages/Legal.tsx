export function TermsPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-slide-up px-4 text-sm text-gray-400 leading-relaxed">
      <h2 className="text-xl font-heading font-bold text-gray-200">Terms of Service</h2>
      <p className="text-[11px] text-gray-600 font-mono">Last updated: June 2026</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">1. Acceptance of Terms</h3>
      <p>By accessing or using SPIA, you agree to these Terms of Service. If you do not agree, do not use the service.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">2. License</h3>
      <p>SPIA is licensed per instance. A Professional license allows use on one server by one user. An Enterprise license allows unlimited users within a single organization. You may not resell, redistribute, or sublicense SPIA without explicit written permission.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">3. Acceptable Use</h3>
      <p>You agree not to use SPIA for illegal purposes, harassment, stalking, or unauthorized access to systems. You are responsible for complying with all applicable laws regarding data privacy and personal information in your jurisdiction.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">4. Third-Party APIs</h3>
      <p>SPIA integrates with third-party APIs (SerpAPI, HIBP, Dehashed, etc.) through keys you provide. You are responsible for complying with each API provider's terms of service. SPIA is not liable for API rate limits, downtime, or changes by third-party providers.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">5. Refunds</h3>
      <p>Professional and Enterprise licenses include a 7-day money-back guarantee. Refund requests after 7 days are handled on a case-by-case basis.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">6. Limitation of Liability</h3>
      <p>SPIA is provided "as is" without warranty. We are not liable for damages arising from the use or inability to use the software.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">7. Contact</h3>
      <p>For questions about these terms, contact support at your licensed email.</p>
    </div>
  )
}

export function PrivacyPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-slide-up px-4 text-sm text-gray-400 leading-relaxed">
      <h2 className="text-xl font-heading font-bold text-gray-200">Privacy Policy</h2>
      <p className="text-[11px] text-gray-600 font-mono">Last updated: June 2026</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">1. Data Collection</h3>
      <p>SPIA does NOT collect, store, or transmit your search queries to our servers. All queries are processed locally on your self-hosted instance. Third-party API calls go directly from your server to the API provider (SerpAPI, HIBP, etc.) — we never see them.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">2. License Validation</h3>
      <p>License activation involves a local hash verification. No personal information is transmitted during license activation. The license key is stored locally on your server.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">3. API Keys</h3>
      <p>The API keys you configure (SerpAPI, HIBP, Dehashed, etc.) are stored locally in an encrypted configuration file on your server. They are never transmitted to third parties other than their respective API endpoints during normal operation.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">4. No Tracking</h3>
      <p>SPIA contains no telemetry, analytics, or tracking code. We have no way of knowing what you search for or how often you use the tool.</p>

      <h3 className="text-base font-heading font-semibold text-gray-300">5. Contact</h3>
      <p>For privacy-related inquiries, contact support at your licensed email.</p>
    </div>
  )
}
