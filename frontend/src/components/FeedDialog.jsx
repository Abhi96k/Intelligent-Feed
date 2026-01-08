import { useState, useEffect } from 'react';

/**
 * FeedDialog Component
 * Modal dialog for creating/editing feeds
 */
function FeedDialog({ isOpen, onClose, onSave, feed = null, businessViews = [], validationResult = null }) {
  const [formData, setFormData] = useState({
    name: '',
    bv_name: '',
    user_query: '',
    schedule_type: 'with_data_refresh',
    schedule_frequency: 'daily',
    schedule_time: '09:00',
    schedule_from_date: '',
    schedule_to_date: '',
    is_active: true,
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (feed) {
      setFormData({
        name: feed.name || '',
        bv_name: feed.bv_name || '',
        user_query: feed.user_query || '',
        schedule_type: feed.schedule_type || 'with_data_refresh',
        schedule_frequency: feed.schedule_frequency || 'daily',
        schedule_time: feed.schedule_time || '09:00',
        schedule_from_date: feed.schedule_from_date || '',
        schedule_to_date: feed.schedule_to_date || '',
        is_active: feed.is_active !== false,
      });
    } else {
      setFormData({
        name: '',
        bv_name: businessViews[0]?.name || '',
        user_query: '',
        schedule_type: 'with_data_refresh',
        schedule_frequency: 'daily',
        schedule_time: '09:00',
        schedule_from_date: '',
        schedule_to_date: '',
        is_active: true,
      });
    }
    setErrors({});
  }, [feed, isOpen, businessViews]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // Clear error when field changes
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Feed name is required';
    if (!formData.bv_name) newErrors.bv_name = 'Please select a Business View';
    if (!formData.user_query.trim()) newErrors.user_query = 'User query is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onSave(formData);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose} />

        {/* Dialog */}
        <div className="inline-block w-full max-w-2xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white rounded-2xl shadow-xl">
          <form onSubmit={handleSubmit}>
            {/* Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-primary-600 to-primary-700">
              <h3 className="text-xl font-semibold text-white">
                {feed ? 'Edit Feed' : 'Create New Feed'}
              </h3>
              <p className="mt-1 text-sm text-primary-100">
                Configure your intelligent feed settings
              </p>
            </div>

            {/* Body */}
            <div className="px-6 py-6 space-y-6">
              {/* Validation Warning */}
              {validationResult && !validationResult.is_valid && (
                <div className="p-4 bg-warning-50 border border-warning-200 rounded-lg">
                  <div className="flex">
                    <svg className="h-5 w-5 text-warning-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-warning-800">Query Validation Warning</h4>
                      <p className="mt-1 text-sm text-warning-700">{validationResult.message}</p>
                      {validationResult.suggestions && validationResult.suggestions.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs font-medium text-warning-800">Suggested queries:</p>
                          <ul className="mt-1 list-disc list-inside text-xs text-warning-700">
                            {validationResult.suggestions.map((s, i) => (
                              <li key={i} className="cursor-pointer hover:text-warning-900" onClick={() => setFormData(prev => ({ ...prev, user_query: s }))}>
                                {s}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Feed Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Feed Name
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className={`mt-1 block w-full rounded-lg border ${errors.name ? 'border-error-300' : 'border-gray-300'} px-4 py-3 shadow-sm focus:border-primary-500 focus:ring-primary-500`}
                  placeholder="e.g., Revenue Drop Alert"
                />
                {errors.name && <p className="mt-1 text-sm text-error-600">{errors.name}</p>}
              </div>

              {/* Business View Selection */}
              <div>
                <label htmlFor="bv_name" className="block text-sm font-medium text-gray-700">
                  Business View
                </label>
                <select
                  id="bv_name"
                  name="bv_name"
                  value={formData.bv_name}
                  onChange={handleChange}
                  className={`mt-1 block w-full rounded-lg border ${errors.bv_name ? 'border-error-300' : 'border-gray-300'} px-4 py-3 shadow-sm focus:border-primary-500 focus:ring-primary-500`}
                >
                  <option value="">Select a Business View</option>
                  {businessViews.map((bv) => (
                    <option key={bv.name} value={bv.name}>
                      {bv.display_name || bv.name}
                    </option>
                  ))}
                </select>
                {errors.bv_name && <p className="mt-1 text-sm text-error-600">{errors.bv_name}</p>}
              </div>

              {/* User Query */}
              <div>
                <label htmlFor="user_query" className="block text-sm font-medium text-gray-700">
                  Analysis Query
                </label>
                <textarea
                  id="user_query"
                  name="user_query"
                  rows={3}
                  value={formData.user_query}
                  onChange={handleChange}
                  className={`mt-1 block w-full rounded-lg border ${errors.user_query ? 'border-error-300' : 'border-gray-300'} px-4 py-3 shadow-sm focus:border-primary-500 focus:ring-primary-500`}
                  placeholder="e.g., Why did revenue drop in Q3 2024 vs previous period?"
                />
                {errors.user_query && <p className="mt-1 text-sm text-error-600">{errors.user_query}</p>}
                <p className="mt-1 text-xs text-gray-500">
                  Enter a natural language question to analyze. Supports both ARIMA (anomaly detection) and Absolute (comparison) queries.
                </p>
              </div>

              {/* Schedule Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Schedule Type
                </label>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="schedule_type"
                      value="with_data_refresh"
                      checked={formData.schedule_type === 'with_data_refresh'}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                    />
                    <span className="ml-3 text-sm text-gray-700">With Data Refresh</span>
                    <span className="ml-2 text-xs text-gray-500">(Runs when data is updated)</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="schedule_type"
                      value="custom"
                      checked={formData.schedule_type === 'custom'}
                      onChange={handleChange}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                    />
                    <span className="ml-3 text-sm text-gray-700">Custom Schedule</span>
                  </label>
                </div>
              </div>

              {/* Custom Schedule Options */}
              {formData.schedule_type === 'custom' && (
                <div className="pl-7 space-y-4 border-l-2 border-primary-100">
                  {/* Date Range */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="schedule_from_date" className="block text-sm font-medium text-gray-700">
                        From Date
                      </label>
                      <input
                        type="date"
                        id="schedule_from_date"
                        name="schedule_from_date"
                        value={formData.schedule_from_date}
                        onChange={handleChange}
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label htmlFor="schedule_to_date" className="block text-sm font-medium text-gray-700">
                        To Date
                      </label>
                      <input
                        type="date"
                        id="schedule_to_date"
                        name="schedule_to_date"
                        value={formData.schedule_to_date}
                        onChange={handleChange}
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                      />
                    </div>
                  </div>
                  
                  {/* Frequency and Time */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="schedule_frequency" className="block text-sm font-medium text-gray-700">
                        Frequency
                      </label>
                      <select
                        id="schedule_frequency"
                        name="schedule_frequency"
                        value={formData.schedule_frequency}
                        onChange={handleChange}
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                      >
                        <option value="hourly">Hourly</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="schedule_time" className="block text-sm font-medium text-gray-700">
                        Time
                      </label>
                      <input
                        type="time"
                        id="schedule_time"
                        name="schedule_time"
                        value={formData.schedule_time}
                        onChange={handleChange}
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Active Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-gray-700">Active</span>
                  <p className="text-xs text-gray-500">Enable or disable this feed</p>
                </div>
                <button
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, is_active: !prev.is_active }))}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${formData.is_active ? 'bg-primary-600' : 'bg-gray-200'}`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${formData.is_active ? 'translate-x-5' : 'translate-x-0'}`}
                  />
                </button>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-gray-50 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                {feed ? 'Save Changes' : 'Create Feed'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default FeedDialog;

