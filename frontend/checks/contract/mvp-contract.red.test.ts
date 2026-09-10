// RED contract check for MVP state protocol.
// This file is intentionally expected to FAIL until the backend/frontend contract is corrected.

import type {
  PandaBackendState,
  PandaChatResponse,
  PandaCurrentPractice,
  PandaReport,
  PandaWeakTopic,
} from "@/contracts/panda";

type Assert<T extends true> = T;

type WeakTopicIsObject = NonNullable<PandaBackendState["weak_topic"]> extends PandaWeakTopic
  ? true
  : false;

type CurrentPracticeIsObject = NonNullable<PandaBackendState["current_practice"]> extends PandaCurrentPractice
  ? true
  : false;

type ReportIsObject = NonNullable<PandaBackendState["report"]> extends PandaReport
  ? true
  : false;

type ResponseHasState = PandaChatResponse extends { state: PandaBackendState }
  ? true
  : false;

export type ContractAssertions = [
  Assert<WeakTopicIsObject>,
  Assert<CurrentPracticeIsObject>,
  Assert<ReportIsObject>,
  Assert<ResponseHasState>
];
