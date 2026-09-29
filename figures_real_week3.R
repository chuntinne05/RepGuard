#!/usr/bin/env Rscript
library(ggplot2)
library(dplyr)

root <- "results/real_week3_json_v1/analysis"
figdir <- file.path(root, "figures")
dir.create(figdir, recursive = TRUE, showWarnings = FALSE)

cap <- read.csv(file.path(root, "capability_matrix.csv")) %>%
  filter(split == "test") %>%
  mutate(subject = factor(subject, levels = rev(sort(unique(subject)))),
         agent = factor(agent, levels = c("qwen3-8b", "gemma2", "llama3-8b", "qwen3-0.6b")))

p_cap <- ggplot(cap, aes(agent, subject, fill = accuracy)) +
  geom_tile(color = "white", linewidth = 0.45) +
  geom_text(aes(label = sprintf("%.1f%%", 100 * accuracy)), size = 3.1) +
  scale_fill_gradient(low = "#f7fbff", high = "#2166ac", limits = c(0, 1), na.value = "grey90") +
  labs(title = "Held-out MMLU-Pro capability by subject", subtitle = "Real model answers; all 14 subjects", x = NULL, y = NULL, fill = "Accuracy") +
  theme_minimal(base_size = 12) +
  theme(panel.grid = element_blank(), plot.title = element_text(face = "bold"))
ggsave(file.path(figdir, "capability_heatmap.png"), p_cap, width = 8.5, height = 6.5, dpi = 220, bg = "white")
ggsave(file.path(figdir, "capability_heatmap.pdf"), p_cap, width = 8.5, height = 6.5, bg = "white")

grid <- read.csv(file.path(root, "qt_grid_results.csv"))
target_cell <- grid %>%
  group_by(method, target, t, q) %>%
  summarise(team_accuracy = mean(team_accuracy), brier_binary = mean(brier_binary),
            unique_expert_success = mean(unique_expert_success, na.rm = TRUE),
            .groups = "drop")
cell <- target_cell %>%
  group_by(method, t, q) %>%
  summarise(team_accuracy = mean(team_accuracy), brier_binary = mean(brier_binary),
            unique_expert_success = mean(unique_expert_success, na.rm = TRUE),
            .groups = "drop") %>%
  mutate(t = factor(t, levels = c("same", "related", "unrelated")),
         q = factor(q, levels = rev(c("oracle", "noisy_025", "noisy_050", "adversarial_040"))))

main_methods <- c("GlobalBeta", "SkillConditioned", "FixedBorrow", "ECRT")
p_qt <- ggplot(filter(cell, method %in% main_methods), aes(t, q, fill = team_accuracy)) +
  geom_tile(color = "white", linewidth = 0.8) +
  geom_text(aes(label = sprintf("%.1f%%", 100 * team_accuracy)), size = 3.1) +
  facet_wrap(~method, ncol = 2) +
  scale_fill_gradient(low = "#fff7ec", high = "#b30000", limits = c(0, 1)) +
  labs(title = "Team accuracy across feedback quality and history relevance",
       subtitle = "Each target subject receives equal weight; same held-out answers across cells",
       x = "History relation to target", y = "Feedback regime", fill = "Team accuracy") +
  theme_minimal(base_size = 11) +
  theme(panel.grid = element_blank(), strip.text = element_text(face = "bold"))
ggsave(file.path(figdir, "qt_team_accuracy_heatmap.png"), p_qt, width = 9, height = 6, dpi = 220, bg = "white")
ggsave(file.path(figdir, "qt_team_accuracy_heatmap.pdf"), p_qt, width = 9, height = 6, bg = "white")

p_brier <- ggplot(filter(cell, method %in% main_methods), aes(t, q, fill = brier_binary)) +
  geom_tile(color = "white", linewidth = 0.8) +
  geom_text(aes(label = sprintf("%.3f", brier_binary)), size = 3.1) +
  facet_wrap(~method, ncol = 2) +
  scale_fill_gradient(low = "#edf8fb", high = "#006d2c") +
  labs(title = "Reputation calibration across feedback and transfer",
       subtitle = "Binary Brier score; lower is better; target subjects weighted equally",
       x = "History relation to target", y = "Feedback regime", fill = "Brier") +
  theme_minimal(base_size = 11) +
  theme(panel.grid = element_blank(), strip.text = element_text(face = "bold"))
ggsave(file.path(figdir, "qt_brier_heatmap.png"), p_brier, width = 9, height = 6, dpi = 220, bg = "white")
ggsave(file.path(figdir, "qt_brier_heatmap.pdf"), p_brier, width = 9, height = 6, bg = "white")

p_expert <- ggplot(filter(cell, method %in% main_methods), aes(t, q, fill = unique_expert_success)) +
  geom_tile(color = "white", linewidth = 0.8) +
  geom_text(aes(label = sprintf("%.1f%%", 100 * unique_expert_success)), size = 3.1) +
  facet_wrap(~method, ncol = 2) +
  scale_fill_gradient(low = "#fff7fb", high = "#7a0177", limits = c(0, 1)) +
  labs(title = "Success when exactly one model answers correctly",
       subtitle = "Per-target rates; target subjects weighted equally",
       x = "History relation to target", y = "Feedback regime", fill = "Success") +
  theme_minimal(base_size = 11) +
  theme(panel.grid = element_blank(), strip.text = element_text(face = "bold"))
ggsave(file.path(figdir, "qt_unique_expert_heatmap.png"), p_expert, width = 9, height = 6, dpi = 220, bg = "white")
ggsave(file.path(figdir, "qt_unique_expert_heatmap.pdf"), p_expert, width = 9, height = 6, bg = "white")

ecrt <- filter(target_cell, method == "ECRT") %>% select(target, t, q, ecrt_acc = team_accuracy)
borrow <- filter(target_cell, method == "FixedBorrow") %>% select(target, t, q, borrow_acc = team_accuracy)
gain <- inner_join(ecrt, borrow, by = c("target", "t", "q")) %>%
  mutate(gain = ecrt_acc - borrow_acc) %>%
  group_by(t, q) %>% summarise(gain = mean(gain), .groups = "drop") %>%
  mutate(t = factor(t, levels = c("same", "related", "unrelated")),
         q = factor(q, levels = rev(c("oracle", "noisy_025", "noisy_050", "adversarial_040"))))
p_gain <- ggplot(gain, aes(t, q, fill = gain)) +
  geom_tile(color = "white", linewidth = 0.8) +
  geom_text(aes(label = sprintf("%+.1f pp", 100 * gain)), size = 3.5) +
  scale_fill_gradient2(low = "#b2182b", mid = "white", high = "#2166ac", midpoint = 0) +
  labs(title = "ECRT minus fixed transfer borrowing", subtitle = "Paired on the same target questions; descriptive mean across target subjects",
       x = "History relation to target", y = "Feedback regime", fill = "Accuracy gain") +
  theme_minimal(base_size = 12) + theme(panel.grid = element_blank())
ggsave(file.path(figdir, "ecrt_vs_fixed_borrow_heatmap.png"), p_gain, width = 8, height = 4.4, dpi = 220, bg = "white")
ggsave(file.path(figdir, "ecrt_vs_fixed_borrow_heatmap.pdf"), p_gain, width = 8, height = 4.4, bg = "white")

attack_path <- file.path(root, "attack_capital_curves.csv")
if (file.exists(attack_path)) {
  attacks <- read.csv(attack_path) %>%
    filter(method %in% main_methods)
  p_attack <- ggplot(attacks, aes(budget_history_tasks, attack_accuracy_loss, color = method)) +
    geom_line(linewidth = 0.9) + geom_point(size = 2) +
    facet_grid(feedback_condition ~ scenario) +
    scale_x_continuous(breaks = c(0, 5, 10, 20, 50, 100)) +
    labs(title = "Attack-capital pilot on real model answers", x = "Historical source tasks",
         y = "Team accuracy loss after forced wrong answer", color = "Method") +
    theme_minimal(base_size = 11)
  ggsave(file.path(figdir, "attack_capital_curves.png"), p_attack, width = 9, height = 7, dpi = 220, bg = "white")
  ggsave(file.path(figdir, "attack_capital_curves.pdf"), p_attack, width = 9, height = 7, bg = "white")
}

cat("Figures saved to", figdir, "\n")
