import { useCallback, useEffect, useRef, useState } from "react";
import {
  GENIE_AUTH_EVENT,
  getGenieAccessToken,
  requestGenie,
  type ChatMessage,
  type HistoryMessage,
} from "../lib/genieApi";

export function useGenieChat() {
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const history = useRef<HistoryMessage[]>([]);
  const controller = useRef<AbortController | null>(null);
  const busy = useRef(false);
  const generation = useRef(0);

  const resetChat = useCallback(() => {
    generation.current += 1;
    controller.current?.abort();
    controller.current = null;
    busy.current = false;
    history.current = [];
    setChat([]);
    setQuery("");
    setError("");
    setIsLoading(false);
  }, []);

  useEffect(() => {
    // Clearing/replacing login credentials also clears this user's chat.
    window.addEventListener(GENIE_AUTH_EVENT, resetChat);
    return () => {
      window.removeEventListener(GENIE_AUTH_EVENT, resetChat);
      generation.current += 1;
      controller.current?.abort();
    };
  }, [resetChat]);

  const sendQuestion = useCallback(async (rawQuestion: string) => {
    const question = rawQuestion.trim();
    if (!question || busy.current) return;
    if (question.length > 4000) {
      setError("Please keep your question under 4,000 characters.");
      return;
    }
    const token = getGenieAccessToken();
    if (!token) {
      setError("Please sign out and sign in again to connect your chat session.");
      return;
    }
    busy.current = true;
    setIsLoading(true);
    setError("");
    setQuery("");
    const currentGeneration = ++generation.current;
    const abortController = new AbortController();
    controller.current = abortController;
    let timedOut = false;
    const timer = window.setTimeout(() => {
      timedOut = true;
      abortController.abort();
    }, 195000);
    const previous = history.current.slice(-12);
    while (
      previous.length > 0 &&
      previous.reduce((sum, item) => sum + item.content.length, question.length) > 48000
    ) previous.splice(0, 2);
    const messages: HistoryMessage[] = [...previous, { role: "user", content: question }];
    setChat((items) => [...items, { id: crypto.randomUUID(), role: "user", content: question }]);
    try {
      const result = await requestGenie(messages, token, abortController.signal);
      if (generation.current !== currentGeneration) return;
      history.current = [
        ...messages,
        { role: "assistant", content: result.answer.slice(0, 16000) },
      ];
      setChat((items) => [...items, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.answer,
        citations: result.citations,
      }]);
    } catch (failure) {
      if (generation.current !== currentGeneration) return;
      setError(timedOut
        ? "Genie took too long. Please try again."
        : failure instanceof TypeError
          ? "Cannot reach the backend. Check that it is running and its URL/CORS settings are correct."
          : failure instanceof Error ? failure.message : "Could not contact Genie.");
      // Only successful question/answer pairs are sent as history on retry.
      setQuery(question);
    } finally {
      window.clearTimeout(timer);
      if (generation.current === currentGeneration) {
        busy.current = false;
        controller.current = null;
        setIsLoading(false);
      }
    }
  }, []);

  return { chat, query, setQuery, sendQuestion, isLoading, error, resetChat };
}

