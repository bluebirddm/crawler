import { toast } from "sonner"

export function useToast() {
  return {
    toast: (props: { title?: string; description?: string; variant?: "default" | "destructive" }) => {
      if (props.variant === "destructive") {
        return toast.error(props.title || props.description || "Error occurred")
      }
      return toast.success(props.title || props.description || "Success")
    }
  }
}