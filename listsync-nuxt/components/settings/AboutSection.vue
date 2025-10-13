<template>
  <Card class="glass-card">
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center gap-3">
        <div class="p-3 rounded-lg bg-muted/10">
          <InfoIcon class="w-5 h-5 text-muted-foreground" />
        </div>
        <div>
          <h3 class="text-lg font-semibold titillium-web-semibold">
            About ListSync
          </h3>
          <p class="text-sm text-muted-foreground">
            System information and resources
          </p>
        </div>
      </div>

      <!-- Links -->
      <div class="space-y-3">
        <p class="text-sm font-medium">Resources</p>

        <a
          href="https://github.com/woahai321/list-sync"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-3 rounded-lg bg-muted/20 hover:bg-muted/30 transition-colors group"
        >
          <div class="flex items-center gap-3">
            <GithubIcon class="w-5 h-5" />
            <div>
              <p class="font-medium">GitHub Repository</p>
              <p class="text-xs text-muted-foreground">View source code and contribute</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
        </a>

        <a
          href="https://discord.gg/Dy5xNzEHKw"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-3 rounded-lg bg-muted/20 hover:bg-muted/30 transition-colors group"
        >
          <div class="flex items-center gap-3">
            <MessageSquareIcon class="w-5 h-5" />
            <div>
              <p class="font-medium">Community Discord</p>
              <p class="text-xs text-muted-foreground">Join our community</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
        </a>

        <a
          href="https://github.com/login?return_to=https://github.com/Woahai321/list-sync/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-3 rounded-lg bg-muted/20 hover:bg-muted/30 transition-colors group"
        >
          <div class="flex items-center gap-3">
            <BugIcon class="w-5 h-5" />
            <div>
              <p class="font-medium">Report an Issue</p>
              <p class="text-xs text-muted-foreground">Found a bug? Let us know</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
        </a>

        <a
          href="https://github.com/Woahai321/list-sync/tree/main/docs"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-3 rounded-lg bg-muted/20 hover:bg-muted/30 transition-colors group"
        >
          <div class="flex items-center gap-3">
            <BookOpenIcon class="w-5 h-5" />
            <div>
              <p class="font-medium">Documentation</p>
              <p class="text-xs text-muted-foreground">Learn how to use ListSync</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
        </a>
      </div>

      <!-- Credits -->
      <div class="p-4 rounded-lg bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
        <div class="flex items-center gap-2 mb-2">
          <HeartIcon class="w-4 h-4 text-danger" />
          <span class="text-sm font-medium">Made with Love</span>
        </div>
        <p class="text-xs text-muted-foreground">
          ListSync is an open-source project built to sync your watchlists across multiple platforms. 
          Special thanks to all contributors and supporters!
        </p>
      </div>

      <!-- System Info -->
      <div class="text-xs text-muted-foreground text-center pt-4 border-t border-border/50">
        <p>Built with Nuxt 3, Vue 3, TailwindCSS, and Python FastAPI</p>
        <p class="mt-1">© 2025 ListSync. Licensed under MIT.</p>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Info as InfoIcon,
  Github as GithubIcon,
  BookOpen as BookOpenIcon,
  Bug as BugIcon,
  MessageSquare as MessageSquareIcon,
  ExternalLink as ExternalLinkIcon,
  Heart as HeartIcon,
} from 'lucide-vue-next'
</script>

