import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Mail, MessageSquare, Link2, Link2Off, RefreshCw, Save } from 'lucide-react'
import { useState } from 'react'
import { fetchApi } from '@/lib/api'
import { toast } from 'sonner'

interface Settings {
  email_enabled: boolean
  slack_enabled: boolean
}

interface SlackStatus {
  connected: boolean
  workspace_id?: string
  workspace_name?: string
  selected_channel_id?: string | null
  selected_channel_name?: string | null
}

interface SlackChannel {
  id: string
  name: string
}

export default function NotificationSettingsPage() {
  const queryClient = useQueryClient()
  const [emailEnabled, setEmailEnabled] = useState<boolean | null>(null)
  const [slackEnabled, setSlackEnabled] = useState<boolean | null>(null)
  const [channels, setChannels] = useState<SlackChannel[]>([])
  const [loadingChannels, setLoadingChannels] = useState(false)

  const { data: settings, isLoading: settingsLoading } = useQuery<Settings>({
    queryKey: ['notification-settings'],
    queryFn: async () => fetchApi('/notifications/settings'),
  })

  const { data: slackStatus, isLoading: slackStatusLoading } = useQuery<SlackStatus>({
    queryKey: ['slack-status'],
    queryFn: async () => fetchApi('/slack/status'),
  })

  const saveSettings = useMutation({
    mutationFn: async (body: Partial<Settings>) => fetchApi('/notifications/settings', {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-settings'] })
      toast.success('Settings saved')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const disconnectSlack = useMutation({
    mutationFn: async () => fetchApi('/slack/disconnect', { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['slack-status'] })
      toast.success('Slack disconnected')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const loadChannels = async () => {
    setLoadingChannels(true)
    try {
      const data = await fetchApi('/slack/channels') as { channels: SlackChannel[] }
      setChannels(data.channels ?? [])
    } catch (err) {
      toast.error('Failed to load channels')
    } finally {
      setLoadingChannels(false)
    }
  }

  const selectChannel = useMutation({
    mutationFn: async (channel: SlackChannel) => fetchApi('/slack/channel', {
      method: 'PUT',
      body: JSON.stringify(channel),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['slack-status'] })
      toast.success('Channel selected')
    },
    onError: (err: Error) => toast.error(err.message),
  })

  const handleSaveSettings = () => {
    const body: Partial<Settings> = {}
    if (emailEnabled !== null) body.email_enabled = emailEnabled
    if (slackEnabled !== null) body.slack_enabled = slackEnabled
    saveSettings.mutate(body)
  }

  const isConnected = slackStatus?.connected ?? false

  if (settingsLoading || slackStatusLoading) {
    return (
      <div className="flex h-full min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-pulse rounded-full bg-muted-foreground/20" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Notification Settings</h1>
        <p className="text-sm text-muted-foreground">
          Configure how you receive notifications
        </p>
      </div>

      {/* Email */}
      <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="flex items-center gap-4 p-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Mail className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium">Email Notifications</h3>
            <p className="text-sm text-muted-foreground">
              Receive notifications via email
            </p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              type="checkbox"
              className="peer sr-only"
              checked={emailEnabled ?? settings?.email_enabled ?? true}
              onChange={(e) => setEmailEnabled(e.target.checked)}
            />
            <div className="h-6 w-11 rounded-full bg-muted after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-background after:transition-all peer-checked:bg-primary peer-checked:after:translate-x-full" />
          </label>
        </div>
      </div>

      {/* Slack */}
      <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="flex items-center gap-4 p-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <MessageSquare className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium">Slack Notifications</h3>
            <p className="text-sm text-muted-foreground">
              {isConnected
                ? `Connected to ${slackStatus?.workspace_name ?? 'Slack'}`
                : 'Connect your Slack workspace'}
            </p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              type="checkbox"
              className="peer sr-only"
              checked={slackEnabled ?? settings?.slack_enabled ?? false}
              onChange={(e) => setSlackEnabled(e.target.checked)}
            />
            <div className="h-6 w-11 rounded-full bg-muted after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-background after:transition-all peer-checked:bg-primary peer-checked:after:translate-x-full" />
          </label>
        </div>

        {isConnected && (
          <div className="border-t px-6 py-4 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm">
                <Link2 className="h-4 w-4 text-emerald-500" />
                <span>
                  Connected to <strong>{slackStatus?.workspace_name}</strong>
                </span>
              </div>
              <button
                onClick={() => disconnectSlack.mutate()}
                className="inline-flex items-center gap-1 text-sm text-destructive hover:underline"
              >
                <Link2Off className="h-4 w-4" />
                Disconnect
              </button>
            </div>

            {slackStatus?.selected_channel_name && (
              <p className="text-sm text-muted-foreground">
                Notifications will be sent to <strong>#{slackStatus.selected_channel_name}</strong>
              </p>
            )}

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Channel</label>
                <button
                  onClick={loadChannels}
                  className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                >
                  <RefreshCw className={`h-3 w-3 ${loadingChannels ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
              {channels.length > 0 && (
                <div className="grid grid-cols-2 gap-2">
                  {channels.map((ch) => (
                    <button
                      key={ch.id}
                      onClick={() => selectChannel.mutate(ch)}
                      className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                        slackStatus?.selected_channel_id === ch.id
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'hover:bg-muted'
                      }`}
                    >
                      # {ch.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {!isConnected && (
          <div className="border-t px-6 py-4">
            <p className="text-sm text-muted-foreground">
              Configure <code>SLACK_CLIENT_ID</code> and <code>SLACK_CLIENT_SECRET</code> in your environment to enable Slack integration.
            </p>
          </div>
        )}
      </div>

      {/* Save */}
      <div className="flex justify-end">
        <button
          onClick={handleSaveSettings}
          disabled={saveSettings.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {saveSettings.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save Settings
        </button>
      </div>
    </div>
  )
}
