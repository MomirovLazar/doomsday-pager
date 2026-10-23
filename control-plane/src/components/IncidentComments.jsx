export default function IncidentComments({
  variant = "list",
  comments,
  commentText,
  onCommentChange,
  onSubmitComment,
  commentLoading,
  commentError,
}) {
  return (
    <>
      {variant === "list" && (
        <div className="incident-comments">
          <h3>Comments ({comments?.length ?? 0})</h3>

          {Array.isArray(comments) && comments.length > 0 ? (
            <div className="comments-list">
              {comments.map((comment) => (
                <div className="comment-item" key={comment.id}>
                  <strong>{comment.author}</strong>
                  <p>{comment.content}</p>
                  <small>{new Date(comment.created_at).toLocaleString()}</small>
                </div>
              ))}
            </div>
          ) : (
            <p>No comments yet.</p>
          )}
        </div>
      )}

      {variant === "form" && (
        <form onSubmit={onSubmitComment} className="comment-form">
          <textarea
            value={commentText}
            onChange={(event) => onCommentChange(event.target.value)}
            placeholder="Write a comment..."
            rows={3}
            maxLength={2000}
            required
          />

          {commentError && <p role="alert">{commentError}</p>}

          <button
            type="submit"
            disabled={commentLoading || !commentText.trim()}
          >
            {commentLoading ? "Sending..." : "Send comment"}
          </button>
        </form>
      )}
    </>
  );
}
