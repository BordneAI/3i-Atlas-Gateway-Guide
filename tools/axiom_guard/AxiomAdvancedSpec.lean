/-!
Axiom Guard advanced governance sketch.

This Lean file is a non-runtime specification artifact for the bounded
sidecar. It records invariants the Python smoke classifier enforces without
making claims about AGI, consciousness, or KB authority.
-/

inductive ClaimClass where
  | negativeNull
  | detectionClaim
  | speculativeClaim
  | governanceCaution
  | unknown
deriving Repr, DecidableEq

inductive DetectionStatus where
  | boundedNonDetection
  | reportedDetection
  | notEvidence
  | requiresReview
deriving Repr, DecidableEq

structure GuardResult where
  classification : ClaimClass
  detectionStatus : DetectionStatus
  proofOfAbsence : Bool
  aaivTier : String
deriving Repr

def NegativeNullInvariant (result : GuardResult) : Prop :=
  result.classification = ClaimClass.negativeNull ->
    result.detectionStatus = DetectionStatus.boundedNonDetection /\
    result.proofOfAbsence = false

def AAIVBoundaryInvariant (result : GuardResult) : Prop :=
  result.aaivTier = "T4-only" \/ result.aaivTier = "not-applicable"

axiom negative_null_sound :
  forall result : GuardResult, NegativeNullInvariant result

axiom aaiv_boundary_sound :
  forall result : GuardResult, AAIVBoundaryInvariant result

