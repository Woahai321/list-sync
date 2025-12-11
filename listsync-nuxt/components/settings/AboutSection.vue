<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center gap-2.5">
        <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
          <InfoIcon class="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <h3 class="text-base font-bold titillium-web-semibold">
            About ListSync
          </h3>
          <p class="text-[10px] text-muted-foreground font-medium">
            System information and resources
          </p>
        </div>
      </div>

      <!-- Links -->
      <div class="space-y-2">
        <p class="text-[10px] font-bold uppercase tracking-wide">Resources</p>

        <a
          href="https://github.com/woahai321/list-sync"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-2 rounded-lg bg-purple-600/10 border border-purple-500/20 hover:border-purple-400/40 hover:bg-purple-600/15 transition-all group"
        >
          <div class="flex items-center gap-2">
            <GithubIcon class="w-4 h-4 text-purple-400" />
            <div>
              <p class="text-sm font-medium">GitHub Repository</p>
              <p class="text-[10px] text-muted-foreground">View source code and contribute</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-3 h-3 text-muted-foreground group-hover:text-purple-400 transition-colors" />
        </a>

        <a
          href="https://discord.gg/Dy5xNzEHKw"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-2 rounded-lg bg-purple-600/10 border border-purple-500/20 hover:border-purple-400/40 hover:bg-purple-600/15 transition-all group"
        >
          <div class="flex items-center gap-2">
            <MessageSquareIcon class="w-4 h-4 text-purple-400" />
            <div>
              <p class="text-sm font-medium">Community Discord</p>
              <p class="text-[10px] text-muted-foreground">Join our community</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-3 h-3 text-muted-foreground group-hover:text-purple-400 transition-colors" />
        </a>

        <a
          href="https://github.com/login?return_to=https://github.com/Woahai321/list-sync/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-2 rounded-lg bg-purple-600/10 border border-purple-500/20 hover:border-purple-400/40 hover:bg-purple-600/15 transition-all group"
        >
          <div class="flex items-center gap-2">
            <BugIcon class="w-4 h-4 text-purple-400" />
            <div>
              <p class="text-sm font-medium">Report an Issue</p>
              <p class="text-[10px] text-muted-foreground">Found a bug? Let us know</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-3 h-3 text-muted-foreground group-hover:text-purple-400 transition-colors" />
        </a>

        <a
          href="https://github.com/Woahai321/list-sync/tree/main/docs"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-between p-2 rounded-lg bg-purple-600/10 border border-purple-500/20 hover:border-purple-400/40 hover:bg-purple-600/15 transition-all group"
        >
          <div class="flex items-center gap-2">
            <BookOpenIcon class="w-4 h-4 text-purple-400" />
            <div>
              <p class="text-sm font-medium">Documentation</p>
              <p class="text-[10px] text-muted-foreground">Learn how to use ListSync</p>
            </div>
          </div>
          <ExternalLinkIcon class="w-3 h-3 text-muted-foreground group-hover:text-purple-400 transition-colors" />
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
        <p class="mt-1">© 2025 Soluify. Licensed under MIT.</p>
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

