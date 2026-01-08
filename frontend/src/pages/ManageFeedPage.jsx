import { useState } from 'react';
import FeedDialog from '../components/FeedDialog';

/**
 * ManageFeedPage Component
 * Page for managing feeds - create, edit, delete
 */
function ManageFeedPage({ feeds, businessViews, onCreateFeed, onUpdateFeed, onDeleteFeed, onValidateQuery }) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingFeed, setEditingFeed] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleOpenCreate = () => {
    setEditingFeed(null);
    setValidationResult(null);
    setSaveSuccess(false);
    setIsDialogOpen(true);
  };

  const handleOpenEdit = (feed) => {
    setEditingFeed(feed);
    setValidationResult(null);
    setSaveSuccess(false);
    setIsDialogOpen(true);
  };

  const handleClose = () => {
    setIsDialogOpen(false);
    setEditingFeed(null);
    setValidationResult(null);
    setSaveSuccess(false);
  };

  const handleSave = async (formData) => {
    // Validate query first
    setIsValidating(true);
    setSaveSuccess(false);
    try {
      const validation = await onValidateQuery(formData.user_query, formData.bv_name);
      setValidationResult(validation);
      
      if (validation.is_valid || validation.can_proceed) {
        // Save the feed
        setIsSaving(true);
        if (editingFeed) {
          await onUpdateFeed({ ...editingFeed, ...formData });
        } else {
          await onCreateFeed(formData);
        }
        setIsSaving(false);
        setSaveSuccess(true);
        // Auto-close dialog after successful save
        setTimeout(() => {
          handleClose();
        }, 500);
      }
    } catch (error) {
      console.error('Validation/Save error:', error);
      setIsSaving(false);
    } finally {
      setIsValidating(false);
    }
  };

  const handleDelete = async (feed) => {
    if (window.confirm(`Are you sure you want to delete "${feed.name}"?`)) {
      await onDeleteFeed(feed.id);
    }
  };

  const getScheduleDisplay = (feed) => {
    if (feed.schedule_type === 'with_data_refresh') {
      return 'With Data Refresh';
    }
    return `${feed.schedule_frequency} at ${feed.schedule_time}`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Manage Feeds</h1>
          <p className="mt-1 text-sm text-gray-500">
            Create and manage your intelligent feed configurations
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add New Feed
        </button>
      </div>

      {/* Feeds Table */}
      {feeds.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No feeds yet</h3>
          <p className="mt-2 text-sm text-gray-500">
            Get started by creating your first intelligent feed.
          </p>
          <button
            onClick={handleOpenCreate}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-primary-600 bg-primary-50 hover:bg-primary-100"
          >
            Create your first feed
          </button>
        </div>
      ) : (
        <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Feed Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Business View
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Query
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Schedule
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Run
                </th>
                <th className="sticky right-0 bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider shadow-[-4px_0_6px_-4px_rgba(0,0,0,0.1)]">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {feeds.map((feed) => (
                <tr key={feed.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`h-2.5 w-2.5 rounded-full mr-3 ${feed.is_active ? 'bg-success-500' : 'bg-gray-300'}`} />
                      <div className="text-sm font-medium text-gray-900">{feed.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {feed.bv_name}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 max-w-xs truncate" title={feed.user_query}>
                      {feed.user_query}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {getScheduleDisplay(feed)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      feed.is_active
                        ? 'bg-success-100 text-success-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {feed.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {feed.last_run ? new Date(feed.last_run).toLocaleString() : 'Never'}
                  </td>
                  <td className="sticky right-0 bg-white px-6 py-4 whitespace-nowrap text-right text-sm font-medium shadow-[-4px_0_6px_-4px_rgba(0,0,0,0.1)]">
                    <button
                      onClick={() => handleOpenEdit(feed)}
                      className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-primary-600 bg-primary-50 rounded-md hover:bg-primary-100 mr-2"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(feed)}
                      className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-error-600 bg-error-50 rounded-md hover:bg-error-100"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Feed Dialog */}
      <FeedDialog
        isOpen={isDialogOpen}
        onClose={handleClose}
        onSave={handleSave}
        feed={editingFeed}
        businessViews={businessViews}
        validationResult={validationResult}
        isValidating={isValidating}
        isSaving={isSaving}
        saveSuccess={saveSuccess}
      />
    </div>
  );
}

export default ManageFeedPage;

