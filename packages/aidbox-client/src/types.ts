import type {
	AddPatch,
	CopyPatch,
	MovePatch,
	RemovePatch,
	ReplacePatch,
	TestPatch,
} from "json-patch";
import type { Resource } from "./fhir-types/hl7-fhir-r4-core";

export type Parameters = [string, string][];
export type Headers = Record<string, string>;

export type AuthProvider = {
	fetch: typeof fetch;
	baseUrl: string;
	revokeSession: () => void;
	establishSession: () => void;
};

export type AidboxReference = {
	id: string;
	resourceType: string;
};

// FIXME: sansara#6557 Generate from IG
export type User = Omit<Resource, "resourceType"> & {
	resourceType: "User";
	email?: string;
};

export type UserInfo = Omit<User, "fhirUser"> & {
	fhirUser?: AidboxReference;
};

export type RequestParams = {
	method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "OPTIONS";
	url: string;
	headers?: Headers;
	params?: Parameters;
	body?: string;
};

export type ResponseWithMeta = {
	response: Response;
	responseHeaders: Headers;
	duration: number;
	request: RequestParams;
};

export type ResourceResponse<T> = ResponseWithMeta & {
	resource: T;
};

/**
 * An error indicating that request didn't met client's expectations and was not sent as a result.
 */
export class RequestError extends Error {
	request: RequestParams;

	constructor(
		msg: string,
		{ cause, request }: { cause?: unknown; request: RequestParams },
	) {
		if (cause) super(msg, { cause });
		else super(msg);
		this.name = "RequestError";
		this.request = request;
	}
}

/**
 * An error indicating an unknown errornous response from the server.
 *
 * Thrown from `client.rawRequest` on any non-successful response code.
 *
 * Only thrown from `client.request` on any non-success code if response body isn't an `OperationOutcome`.
 */
export class ErrorResponse extends Error {
	responseWithMeta: ResponseWithMeta;

	constructor(msg: string, cause: ResponseWithMeta) {
		super(msg);
		this.responseWithMeta = cause;
		this.name = "ErrorResponse";
	}
}

/// FHIR HTTP method params

export type ReadOptions = {
	type: string;
	id: string;
	mimeType?: string;
};

export type VReadOptions = ReadOptions & {
	vid: string;
};

export type SearchTypeOptions = {
	type: string;
	query: Parameters;
};

export type SearchSystemOptions = {
	query: Parameters;
};

export type SearchCompartmentOptions = {
	query: Parameters;
	type: string;
	compartment: string;
	compartmentId: string;
};

/**
 * The `Bundle.link` relation of the page to follow.
 */
export type SearchPageRelation =
	| "next"
	| "previous"
	| "prev"
	| "first"
	| "last";

/**
 * The minimal shape of a searchset `Bundle` a continuation link is read from.
 */
export type SearchPageBundle = {
	link?: { relation: string; url: string }[];
};

export type SearchPageOptions =
	| { url: string }
	| { bundle: SearchPageBundle; relation?: SearchPageRelation };

export type CreateOptions<T> = {
	type: string;
	resource: T;
};

export type ConditionalCreateOptions<T> = {
	type: string;
	resource: T;
	searchParameters: Parameters;
};

export type UpdateOptions<T> = {
	type: string;
	resource: T;
	id: string;
};

export type ConditionalUpdateOptions<T> = {
	type: string;
	resource: T;
	searchParameters: Parameters;
};

export type PatchOptions = {
	type: string;
	id: string;
	patch: (
		| AddPatch
		| RemovePatch
		| ReplacePatch
		| MovePatch
		| CopyPatch
		| TestPatch
	)[];
};

export type ConditionalPatchOptions = {
	type: string;
	searchParameters: Parameters;
	patch: (
		| AddPatch
		| RemovePatch
		| ReplacePatch
		| MovePatch
		| CopyPatch
		| TestPatch
	)[];
};

export type DeleteOptions = {
	type: string;
	id: string;
};

export type ConditionalDeleteOptions = {
	type?: string;
	searchParameters: Parameters;
};

export type DeleteHistoryVersionOptions = {
	type: string;
	id: string;
	vid: string;
};

export type HistoryInstanceOptions = {
	type: string;
	id: string;
};

export type HistoryTypeOptions = {
	type: string;
};

export type HistorySystemOptions = Record<string, never>;

export type OperationOptions<T = unknown> = {
	type: string;
	id?: string;
	operation: `$${string}`;
	resource?: T;
};

export type ValidateOptions<T> = Omit<OperationOptions<T>, "operation"> & {
	resource: T;
};

export type CapabilitiesOptions = {
	mode: "full" | "normative" | "terminology";
};

export type BatchOptions<TBundle> = {
	format: string;
	bundle: TBundle & {
		type: "batch";
	};
};

/** Result of a ViewDefinition $materialize operation. */
export type MaterializeResult = {
	resourceType: "Parameters";
	parameter?: Array<{ name: string; valueString?: string; valueCode?: string }>;
};

export type TransactionOptions<TBundle> = {
	format: string;
	bundle: TBundle & {
		type: "transaction";
	};
};

/** A single file to be imported by an Aidbox bulk import operation. */
export type BulkImportInput = {
	url: string;
	resourceType: string;
};

/** Body of an Aidbox `POST /v2/fhir/$import` submission. */
export type BulkImportRequest = {
	/** Caller-supplied operation id; Aidbox generates one when omitted. */
	id?: string;
	contentEncoding?: "gzip" | "plain";
	inputs: BulkImportInput[];
	update?: boolean;
	allowedRetryCount?: number;
};

/** Handle of an accepted bulk import operation. */
export type BulkImportHandle = {
	id: string;
	/** Absolute, same-origin `/v2/$import/<id>` status location returned by the server. */
	statusUrl: string;
};

/**
 * Server-reported state of a single bulk import input.
 *
 * Unknown server fields are preserved as-is.
 *
 * `status` is optional: the server may not have assigned one yet right after the submission.
 * Beside the listed values, further server states such as `requested` and `ready` have been observed, so any string may appear.
 */
export type BulkImportInputStatus = {
	url: string;
	resourceType: string;
	status?: "waiting" | "in-progress" | "done" | (string & {});
	outcome?: "succeeded" | "failed" | (string & {});
	result?: { "imported-resources"?: number } & Record<string, unknown>;
	error?: { message?: string } & Record<string, unknown>;
} & Record<string, unknown>;

/**
 * Server-reported state of a bulk import operation.
 *
 * Unknown server fields are preserved as-is.
 *
 * Beside the listed `status` values, further server states such as `requested` and `ready` have been observed, so any string may appear.
 */
export type BulkImportStatus = {
	type?: string;
	status: "in-progress" | "done" | (string & {});
	outcome?: "succeeded" | "failed" | (string & {});
	contentEncoding?: string;
	allowedRetryCount?: number;
	inputs: BulkImportInputStatus[];
	result?: {
		message?: string;
		"total-files"?: number;
		"total-imported-resources"?: number;
	} & Record<string, unknown>;
	error?: { message?: string } & Record<string, unknown>;
} & Record<string, unknown>;

/// Aidbox $batch-validate

/**
 * A raw FHIR `Parameters.parameter` entry.
 *
 * Additional members are kept as-is so that server or client parameters this SDK does not model are preserved.
 */
export type FhirParameter = { name: string } & Record<string, unknown>;

/** A raw FHIR `Parameters` resource. */
export type ParametersResource = {
	resourceType: "Parameters";
	parameter?: FhirParameter[];
} & Record<string, unknown>;

/**
 * Start options of the Aidbox `$batch-validate` operation.
 *
 * `since` is required by the operation and is sent as the `_since` `valueInstant` parameter.
 * `parameters` is a pass-through list of additional `Parameters.parameter` entries for options this SDK does not model.
 */
export type BatchValidateRequest = {
	type: string;
	since: string;
	until?: string;
	profiles?: string[];
	respondAsync?: boolean;
	parameters?: FhirParameter[];
};

/**
 * One aggregated validation issue of a `$batch-validate` summary.
 *
 * Parts that this client does not model stay reachable through the summary's raw `parameters`.
 */
export type BatchValidateIssue = {
	id?: string;
	code?: string;
	expression?: string;
	count?: number;
	diagnostics?: string;
	invalidResourcesUrl?: string;
};

/**
 * A `$batch-validate` summary report.
 *
 * `parameters` keeps the raw `Parameters` resource, so parameters this SDK does not model stay reachable.
 */
export type BatchValidateSummary = {
	taskId: string;
	validated?: number;
	valid?: number;
	invalid?: number;
	bytes?: number;
	invalidResourcesUrl?: string;
	issues: BatchValidateIssue[];
	parameters: ParametersResource;
};

/** A handle of an asynchronous `$batch-validate` task. */
export type BatchValidateTaskHandle = {
	taskId: string;
	statusUrl: string;
};

/**
 * The state of a `$batch-validate` task.
 *
 * Aidbox answers a status request of an unfinished task with an informational `OperationOutcome` that carries the progress, and only a finished task with a summary.
 */
export type BatchValidateStatus =
	| { kind: "summary"; summary: BatchValidateSummary }
	| { kind: "in-progress"; outcome: unknown };

/** The outcome of starting `$batch-validate`: a finished summary, or a handle of an accepted asynchronous task. */
export type BatchValidateStart =
	| { kind: "summary"; summary: BatchValidateSummary }
	| { kind: "task"; handle: BatchValidateTaskHandle };

/**
 * One invalid resource of a `$batch-validate` drill-down report.
 *
 * Parts that this client does not model stay reachable through the report's raw `parameters`.
 */
export type BatchValidateInvalidResource = {
	fullUrl?: string;
	resource?: unknown;
	outcome?: unknown;
};

/** A page of the `$batch-validate` invalid-resources report. */
export type BatchValidateInvalidResourcesReport = {
	total?: number;
	selfUrl?: string;
	/** Present only when the server supplies a `next` parameter. */
	nextUrl?: string;
	resources: BatchValidateInvalidResource[];
	parameters: ParametersResource;
};

/**
 * Selection of a `$batch-validate` invalid-resources page.
 *
 * Either a task handle with paging options, or a `self`, `next` or `invalid-resources` URL taken from a summary or report.
 */
export type BatchValidateInvalidResourcesOptions =
	| {
			handle: BatchValidateTaskHandle;
			count?: number;
			page?: number;
			issues?: string[];
	  }
	| { url: string };

/** The result of cancelling a `$batch-validate` task, with the server's response body preserved. */
export type BatchValidateCancelResult = ResponseWithMeta & {
	outcome?: unknown;
};
