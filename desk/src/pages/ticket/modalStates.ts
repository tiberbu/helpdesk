import { ref } from "vue";

export const showAssignmentModal = ref(false);
export const showEmailBox = ref(false);
export const showCommentBox = ref(false);
export const showInternalNoteBox = ref(false);
export function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false;
  }
  if (showInternalNoteBox.value) {
    showInternalNoteBox.value = false;
  }
  showEmailBox.value = !showEmailBox.value;
}
export function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false;
  }
  if (showInternalNoteBox.value) {
    showInternalNoteBox.value = false;
  }
  showCommentBox.value = !showCommentBox.value;
}
export function toggleInternalNoteBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false;
  }
  if (showCommentBox.value) {
    showCommentBox.value = false;
  }
  showInternalNoteBox.value = !showInternalNoteBox.value;
}
